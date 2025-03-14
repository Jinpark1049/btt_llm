import json
column_order =  ['folder_name', 'file_name', 'lang', 'exflag', 'glpflag', 'title', 'id', 'material', 'animal', 'animal_date', 'path', 'guide1', 'guide2', 'test_sdate', 'test_fdate', 'exam_sdate', 'exam_fdate', 'sdname', 'pathologist', 'test_item', 'test_group', 'summary', 'conclusion']

keyword_dict = {"GLP": ["GLP", "GLP 적합진술서", "GLP COMPLIANCE STATEMENT", "GLP適合陳述書", "Good Laboratory Practice Regulations", "GLP 준수 기준", "Good Laboratory Practice Regulations"],
                "guide2": ["시험기준", "Regulatory Guidelines", "REGULATORY GUIDELINES", "ガイドライン", "본 시험은 다음의 시험기준에 근거하여 실시하였다.", "下記のガイドラインに準拠して実施した", "This study was conducted in accordance with the following guidelines"],
                "sdname": ["시험 책임자","시험책임자", "STUDY DIRECTOR", "試験責任者", "Study Director"],
                "study_date": ["Study Schedule", "시험일정", "試験スケジュール", "Study initiation", "Experimental start", "Validation start", "Validation of analytical method", "Experimental completion", "study completion", "시험개시일", "실험개시일", "실험종료일", "시험종료일", "試験開始日", "実験開始日", "動物入手日", "実験完了日", "試験完了日", "皮膚反応"],
                "material": ['시험물질, 시험재료 및 방법', '시험물질명' 'MATERIALS AND METHODS', 'TEST SUBSTANCE', '被験物質'],
                
                "animal": ['종 및 계통', '동물', 'animal', '動物'], 
                "animal_date": ["시험일정", "동물입수일", "Animal receipt", "Study Schedule", "試験スケジュール", "動物入手日"],
                "path": ["투여", "투여경로", "Dosing", "Route", "投与", "投与経路"],

                "pathologist": ['Pathologist', '분담책임자', "分担責任者", "試験担当者"], # 병리는 제외 텍스트 정보가 너무 많아짐.
                "summary": ["Purpose", "시험목적", "試験目的"],
                "conclusion": ["결론","CONCLUSION", "考察および結論"],
                
                "test_item": [],
                "test_group": ['기타', '효능시험', '일반독성', '국소독성', '면역독성', '유전독성', '광독성', '안전성약리', '생식독성', 'PK시험', 'TK시험', '조제물분석', '안정성약리', '발암성', '수생생태독성', '독성시험', '대체독성', '복귀돌연변이시험']}

parser_prompt = {"title_lang":"""
        Given the following page content:
        \"\"\"{text}\"\"\"

        Determine Title, Test Number, Language
        - Language can be English, Korean, Japanse
        - You must not translate the language
        - If the provided information is insufficient to form a response, simply state "none"
        - Return **only** Title:, Test Number: 
        
        Examples)
        - be cautious that example can be different from real text but here are some of the examples        
        if text be like:
        ' \n- 1/45 - \n  \n \n \n최종보고서 \n \n Sodium chloride, Ethylmethanesulfonate, \nCyclophosphamide, Methylmethanesulfonate, \nBenzo(a)pyrene, 3-Methylcholanthrene, Ethylnitrosourea, \n및 4-Nitroquinoline N-oxide의 포유류 배양세포를 이용한 \n체외 유전자 돌연변이시험 \n \n \n \n \n시험번호: R20008 \n  \n㈜바이오톡스텍 \n우28115 충청북도 청주시 청원구 오창읍 연구단지로 53 \n \n'
        your answer must be:
        Title: Sodium chloride, Ethylmethanesulfonate, Cyclophosphamide, Methylmethanesulfonate, Benzo(a)pyrene, 3-Methylcholanthrene, Ethylnitrosourea, 및 4-Nitroquinoline N-oxide의 포유류 배양세포를 이용한 체외 유전자 돌연변이시험
        Test Number: R20008
        Language: 한국어
        
        if text be like:
        '- 1/42 - \n \n \n \n \n最終報告書 \n \n \n \nKUH-221-1kg粒のモルモットを用いる \n皮膚感作性試験 (Buehler法) \n \n \n試験番号：J22099 \n \n \n \nBiotoxtech Co., Ltd. \n53, Yeongudanji-ro, Ochang-eup, Cheongwon-gu, Cheongju-si, \nChungcheongbuk-do, 28115, Republic of Korea \n'
        your answer must be:
        Title: KUH-221-1kg粒のモルモットを用いる皮膚感作性試験 (Buehler法)
        Test Number: J22099
        Language: 일본어

        if text be like:
        '- 1/39 - \n \n \nFINAL REPORT \n \nBacterial Reverse Mutation Test of OK-5101 20SC \n \nStudy No.: J22100 \n \n \n \n \nBiotoxtech Co., Ltd. \n53, Yeongudanji-ro, Ochang-eup, Cheongwon-gu, Cheongju-si,  \nChungcheongbuk-do, 28115, Republic of Korea \n \n'
        your answer must be:
        Title: Bacterial Reverse Mutation Test of OK-5101 20SC
        Test Number: J22100
        Language: 영어

        Return **only** Title:, Test Number:, Language:
        For language, write in Korean 영어, 한국어, 일본어
        DO NOT include anythingelse
        """,
        "glp": {"glpflag":"Determine whether the following text explicitly states compliance with Good Laboratory Practice (GLP) regulations: {text} Instructions: - If the text explicitly mentions adherence to GLP regulations, return **GLP**. - If the text explicitly states 'Non-GLP,' return **Non-GLP**. - Do not infer compliance—base the answer strictly on explicit mentions. - Only write 'GLP' or 'Non-GLP' for Answer", 
                "guide1": "Extract all GLP-related regulations from the following text: {text} Instructions: - Focus on the given keywords: {keyword}. - List the extracted regulations separated by '|' without adding '|' at the end. - Do not include '-' in front of the regulations. - If no GLP-related regulations are found, return **none**."},   
        "animal": {"animal":  "Extract the name of the animal species used for the experiment from the following text: {text} Instructions: - First, try to find animal species from the given title: {keyword}. - The text may be in Korean, English, or Japanese. - Maintain the original language of the extracted name; do not translate it. - Return only the animal. - do not include explanation. - If no animal is found, return **none**.", 
                   "animal_date": "Extract the animal receipt dates from the given text: {text}  ### Instructions:  - Focus on the given keywords: {keyword}.  - The text may be in Korean, English, or Japanese. Maintain the original language of extracted terms.  - Return dates in the format **YYYY-MM-DD** (e.g., 2022-06-08).  - If no sufficient information is found in the text, return **none**. - find only one date ### Output format: [YYYY-MM-DD] or **none**  Return only the extracted details—no explanations.", 
                   "path": "Extract the dosing route of the drug from the given text: {text} Instructions: - First, try to find dosing route from the given title: {keyword}. If there is no sufficient information, utilize the given text. - The text may be in Korean, English, or Japanese. Maintain the original language of extracted terms. - If path is not found, return **none**. Return only the dosing route (e.g., Oral, 経皮, 정맥) —no explanations."},
        "test": {"test_group":  "Extract the category from the given text: {text} Instructions: - find the most relevant category from given options: {keyword}. If there is no sufficient information, return **기타**. - The text may be in Korean, English, or Japanese. - Return only the category from the provided options details—no explanations.", 
                 "test_item": """ Given the input {text}, please rewrite it following these specific test name:
                1. Test Name Formatting Rules: Use the format: [Purpose] + "Test" (e.g., "Acute Toxicity Test", "Skin Sensitization Test").
                If applicable, specify the test type (e.g., "In vivo", "In vitro") before the test name (e.g., "In vivo Antitumor Efficacy Test").
                If a standardized test method is used, include it in parentheses (e.g., "Skin Sensitization Test (LLNA, Maximization, Buehler method)").
                
                2. Test Classification System
                Categorize the test appropriately:
                Toxicity Tests (Acute, Subacute, Chronic)
                Genotoxicity Tests (Mutation, Chromosomal Aberration)
                Safety Assessment Tests (Pharmacology, Toxicokinetics, Drug Metabolism)
                Efficacy Evaluation Tests (Anticancer, Diabetes, Obesity, Antioxidant, Immunity)
                Irritation Tests (Skin, Ocular, Oral Mucosa)
                Other Tests (Bioanalysis, Stability Tests)
                
                3. Detailed Test Description Formatting
                Include the test subject (e.g., Rat, Mouse, Beagle, Rabbit).
                Specify the test duration (e.g., 2 weeks, 4 weeks, 13 weeks, 26 weeks, 52 weeks).
                Use standardized terms for test methodologies (e.g., "Dose Range Finding (DRF) Study").
                Define evaluation criteria (e.g., survival rate, histopathological analysis).
                
                4. Standardized Terminology and Abbreviations
                Use internationally recognized abbreviations (e.g., PK for Pharmacokinetics, TK for Toxicokinetics).
                Maintain consistent terminology (e.g., always refer to "Efficacy Test" or "Toxicity Test").
                Follow established test guidelines (e.g., OECD, FDA, ICH).
                Please apply these rules and rewrite the given text accordingly.
                
                - If there is no sufficient information, return **none**.
                - Return only the test name from the provided options details—no explanations."""},
        "guide2": "Extract all regulatory guidelines from the following text:  {text}  Instructions:  - Focus on the given keywords: {keyword}.  - List the extracted guidelines separated by '|' without adding '|' at the end.  - Do not include '-' in front of the regulations.  - Ensure the extracted guidelines are not confused with Good Laboratory Practice Regulations.  - If no regulatory guidelines are found, return **none**.",
        "study_date": "Extract the following dates from the given text: {text} Instructions: - Focus on the given keywords: {keyword}. - The text may be in Korean, English, or Japanese. Maintain the original language of extracted terms. - Return dates in the format: **YYYY-MM-DD**. - Ensure the correct order: - **Experimental start date** comes before **Study start date**. - **Experimental completion date** is later than **Study end date**. - If a date is not found, return **none**. Output format: Study start: [YYYY-MM-DD or none] Study end: [YYYY-MM-DD or none] Experimental start: [YYYY-MM-DD or none] Experimental completion: [YYYY-MM-DD or none]. Return only the extracted details—no explanations.",
        "material": "Extract the substance material from the given text: {text} Instructions: - First, try to find substance material from the given title: {keyword}. If there is no sufficient information, utilize the given text. - The text may be in Korean, English, or Japanese. Maintain the original language of extracted terms. - If a substance or material is not found, return **none**. - If there are multiple materials found list the extracted materials separated by '|' without adding '|' at the end. Return only the extracted details—no explanations.",
        "sdname": "Extract the name of the study director from the following text: {text} Instructions: - Focus on the given keywords: {keyword}. - The text may be in Korean, English, or Japanese. - Maintain the original language of the extracted name; do not translate it. - Return only the study director's name. - do not include explanation. - If no name is found, return **none**.",
        "pathologist": "Extract the name of the pathologist from the following text: {text} Instructions: - Focus on the given keywords: {keyword}. - The text may be in Korean, English, or Japanese. - Maintain the original language of the extracted name; do not translate it. - Return only the name. - do not include explanation - If no name is found, return **none**.",
        "summary": "Extract the summary from the given text: {text} Instructions: - Focus on the given keywords: {keyword}. - The text may be in Korean, English, or Japanese. Maintain the original language of extracted terms. - If a summary is not found, return **none**. - only write summary text. Return only the extracted details—no explanations.",
        "conclusion": "Extract the conclusion from the given text: {text} Instructions: - Focus on the given keywords: {keyword}. - The text may be in Korean, English, or Japanese. Maintain the original language of extracted terms. - If a conclusion is not found, return **none**. - only write conclusion text. Return only the extracted details—no explanations."
        }

data_list = {"column_order":column_order, "keyword_dict":keyword_dict, "parser_prompt": parser_prompt}

if __name__ == "__main__":
    # JSON 파일로 저장
    with open('data.json', 'w', encoding='utf-8') as json_file:
        json.dump(data_list, json_file, ensure_ascii=False, indent=4) 
    print("JSON 파일이 생성되었습니다.")