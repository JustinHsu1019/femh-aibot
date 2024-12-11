import os
import sys

import voyageai
import weaviate
from langchain.embeddings import OpenAIEmbeddings

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import utils.config_log as config_log

config, logger, CONFIG_PATH = config_log.setup_config_and_logging()
config.read(CONFIG_PATH)

voyage_api_key = config.get('VoyageAI', 'api_key')
wea_url = config.get('Weaviate', 'weaviate_url')
PROPERTIES = ['uuid', 'title', 'content']

os.environ['OPENAI_API_KEY'] = config.get('OpenAI', 'api_key')


def rerank_with_voyage(query, documents, api_key):
    vo = voyageai.Client(api_key=api_key)
    reranking = vo.rerank(query, documents, model='rerank-2', top_k=5)

    top_documents = [result.document for result in reranking.results]

    return top_documents


class WeaviateSemanticSearch:
    def __init__(self, classnm):
        self.url = wea_url
        self.embeddings = OpenAIEmbeddings(chunk_size=1, model='text-embedding-3-large')
        self.client = weaviate.Client(url=wea_url)
        self.classnm = classnm

    def aggregate_count(self):
        return self.client.query.aggregate(self.classnm).with_meta_count().do()

    def get_all_data(self, limit=100):
        if self.client.schema.exists(self.classnm):
            result = self.client.query.get(class_name=self.classnm, properties=PROPERTIES).with_limit(limit).do()
            return result
        else:
            raise Exception(f'Class {self.classnm} does not exist.')

    def delete_class(self):
        self.client.schema.delete_class(self.classnm)

    def hybrid_search(self, query, num, alpha):
        query_vector = self.embeddings.embed_query(query)
        vector_str = ','.join(map(str, query_vector))
        gql_query = f"""
        {{
            Get {{
                {self.classnm}(hybrid: {{query: "{query}", vector: [{vector_str}], alpha: {alpha} }}, limit: {num}) {{
                    title
                    content
                    _additional {{
                        distance
                        score
                    }}
                }}
            }}
        }}
        """
        search_results = self.client.query.raw(gql_query)

        if 'errors' in search_results:
            raise Exception(search_results['errors'][0]['message'])

        results = search_results['data']['Get'][self.classnm]
        return results


def search_do(input_, alp):
    searcher = WeaviateSemanticSearch("Femhdata")
    results = searcher.hybrid_search(input_, 100, alpha=alp)

    result_li = []
    for _, result in enumerate(results, 1):
        result_li.append(result['content'])

    return rerank_with_voyage(input_, result_li, voyage_api_key)


if __name__ == '__main__':
    vdb = "Femhdata"
    client = WeaviateSemanticSearch(vdb)

    # 統計筆數
    count_result = client.aggregate_count()
    print(count_result)

    # 輸出所有資料
    # data_result = client.get_all_data()
    # print(data_result)

    # 刪除此向量庫
    # client.delete_class()

    # An alpha of 1 is a pure vector search
    # An alpha of 0 is a pure keyword search
    # quest = "幫我找專任助理"
    # print(search_do(quest, alp=0.5))
