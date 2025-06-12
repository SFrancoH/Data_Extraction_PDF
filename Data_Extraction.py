import os
import re
import fitz  # PyMuPDF
import json
import pandas as pd

def get_pdf_file_paths(directory):
    file_paths = []
    for file in os.listdir(directory):
        full_path = os.path.join(directory, file)
        if os.path.isfile(full_path) and file.lower().endswith('.pdf'):
            file_paths.append(full_path)
    return file_paths

def read_local_pdfs(pdf_path_list):
    content_dict = {}
    for pdf_path in pdf_path_list:
        try:
            file_name = os.path.basename(pdf_path)
            text = ""
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()

            name_parts = re.split(r'[_\-]', file_name)
            if len(name_parts) >= 3:
                month = name_parts[2]
            else:
                month = ""

            content_dict[file_name] = {
                "content": text.strip(),
                "month": month,
            }
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
    return content_dict

def extract_usage_by_number(content_dict):
    table = []
    pattern = re.compile(
        r'(\d{3}\.\d{3}\.\d{4})[\s\S]{0,100}?Total usage\s+([0-9.,]+)',
        re.IGNORECASE
    )
    for file_name, data in content_dict.items():
        text = data["content"]
        month = data.get("month", "")
        matches = pattern.findall(text)
        for phone_number, usage in matches:
            usage = usage.replace(',', '')
            try:
                usage_float = float(usage)
                table.append({
                    "Month": month,
                    "Phone Number": phone_number,
                    "Usage": usage_float
                })
            except ValueError:
                continue
    return table

def extract_usage_with_gb(content_dict):
    usage_table = []
    pattern = re.compile(
        r'(\d{3}\.\d{3}\.\d{4})[\s\S]{0,100}?([0-9.,]+)GB',
        re.IGNORECASE
    )
    for file_name, data in content_dict.items():
        text = data["content"]
        month = data.get("month", "")
        matches = pattern.findall(text)
        for phone, usage in matches:
            usage = usage.replace(',', '')
            try:
                usage_float = float(usage)
                usage_table.append({
                    "Month": month,
                    "Phone Number": phone,
                    "Usage": usage_float
                })
            except ValueError:
                continue
    return usage_table

def save_to_json(data, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f"JSON saved to: {output_path}")
    except Exception as e:
        print(f"Error saving JSON: {e}")

if __name__ == "__main__":

    input_directory = r'Directory'

    pdf_paths = get_pdf_file_paths(input_directory)
    parsed_pdfs = read_local_pdfs(pdf_paths)

    usage_no_gb = extract_usage_by_number(parsed_pdfs)
    usage_with_gb = extract_usage_with_gb(parsed_pdfs)

    df_v1 = pd.DataFrame(usage_no_gb)
    df_v2 = pd.DataFrame(usage_with_gb)
    final_df = pd.concat([df_v1, df_v2], ignore_index=True)

    save_to_json(final_df.to_dict(orient="records"), "usage_data.json")

    print("Combined usage data preview:")
    print(final_df.head())
