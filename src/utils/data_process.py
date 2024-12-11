import os
from pdf2image import convert_from_path
import pytesseract

# 設定來源資料夾和輸出檔案名稱
input_folder = "data/"
output_file = "data/merged_output.txt"

# 確保 Tesseract 安裝路徑（如果是自訂路徑）
pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"

# 初始化空的字串來儲存所有 PDF 的內容
all_text = []

# 確保目錄存在
if not os.path.exists(input_folder):
    print(f"資料夾 {input_folder} 不存在，請確認路徑！")
    exit()

# 遍歷資料夾內所有檔案
for filename in sorted(os.listdir(input_folder)):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(input_folder, filename)
        print(f"正在處理: {pdf_path}")

        try:
            # 將 PDF 每一頁轉成圖片
            pages = convert_from_path(pdf_path, dpi=300)

            pdf_text = ""
            for i, page in enumerate(pages):
                print(f"正在 OCR 第 {i + 1} 頁...")
                # 使用 OCR 從圖片提取文字
                page_text = pytesseract.image_to_string(page, lang="eng")  # 調整 lang 為需要的語言
                pdf_text += page_text.strip() + "\n\n"

            all_text.append(pdf_text.strip())
        except Exception as e:
            print(f"處理檔案 {filename} 時出錯: {e}")

# 將所有內容以 "\n\n" 分隔符號合併
final_text = "\n\n".join(all_text)

# 將合併的內容寫入輸出檔案
try:
    with open(output_file, "w", encoding="utf8") as f:
        f.write(final_text)
    print(f"所有 PDF 的內容已成功寫入 {output_file}")
except Exception as e:
    print(f"寫入檔案時出錯: {e}")
