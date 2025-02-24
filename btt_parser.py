import fitz  # PyMuPDF
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_ollama import OllamaLLM
import re
from util.utils import *
import time
import json
from langchain_core.output_parsers import StrOutputParser


class Biollm:
    def __init__(self, data:str ='/home/workspace/btt/util/data.json', model:str ="mistral:latest"):
        
        with open(data, 'r') as json_file:
            self.data = json.load(json_file)

        self.keyword_dict = self.data['keyword_dict'] 
        # Initialize the parsing data
        self.parsed_data = {column: "none" for column in self.data['column_order']}
        # Prompt        
        self.prompts = self.data['parser_prompt']
        # searching column
        self.searching_column = ["GLP", "guide2", "sdname", "study_date", "summary", "conclusion", "material", "pathologist", "animal", "animal_date", "path"]
        self.relevant_pages = {column: [] for column in self.searching_column}  

        # Model load
        self.llm = OllamaLLM(model=model, temperature=0, device='cuda')
    
    def run(self, pdf_path: str):
        
        start_time = time.time()
        print(f"extraction has started")

        self.doc = fitz.open(pdf_path)
        self._extract_file_info(pdf_path)        
        
        self.find_relevant_pages(self.searching_column)
        self.parse_llm()
        
        end_time = time.time()
        print(f"processing took: {end_time-start_time}s")
    
    def run_one(self, pdf_path: str, search: str = None, llm_search = True):
        ## test는 한번 못구함.
        result_info= {
            'GLP': ["glpflag", 'guide1'],
            'animal': ['animal', 'animal_date', 'path'],
            'study_date':['exam_sdate', 'exam_fdate','test_sdate','test_fdate'],
            'material': ['material'],
            'guide2': ['guide2'],
            'sdname': ['sdname'],
            'pathologist': ['pathologist'],
            'summary': ['summary'],
            'conclusion': ['conclusion'],
        }
        
        print(f"Extraction has started")  
        if search not in self.searching_column:
            print('search is not available')
            return 
        elif search in ["animal", "animal_date", "path"]: # grouped execution
            search = ["animal", "animal_date", "path"]
            key_ = "animal" 
        else:
            key_ = search
            search = [search]
          
        start_time = time.time()
       
        self.doc = fitz.open(pdf_path)
        
        self.find_relevant_pages(columns = search, llm=llm_search)   
        self.parse_llm(key_)
        
        end_time = time.time()
        print(f"processing took: {end_time-start_time}s")
        return {key: self.parsed_data[key] for key in result_info[key_]}
        
    def _extract_file_info(self, pdf_path: str):
        
        pattern = r'/(\d{4})/([^/]+\.pdf)$'
        match = re.search(pattern, pdf_path)
        if match:
            self.parsed_data['folder_name'] = match.group(1)
            self.parsed_data['file_name'] = match.group(2)
            self.parsed_data['exflag'] = "none"
        else:
            print("No year or PDF file name found.")

    def find_relevant_pages(self, columns: list, llm = False):
    
        prompt = PromptTemplate(
            input_variables=["text", "keyword"],
            template=""" Given the following page content: {text} Determine if the page contains relevant content based on the keywords or related synonyms: {keyword}.  
            - If the page contains any of the keywords or related content, return **"relevant"**.  
            - Otherwise, return **"not relevant"**.  
            - Output only **"relevant"** or **"not relevant"**, with no explanations.  
            """
            )
        chain = prompt | self.llm

        # Initialize with empty lists
        for page_num, page in enumerate(self.doc):
            page_text = page.get_text()

            # Skip pages with too many "·" characters
            if page_text.count("·") > 200:
                continue
            # Check for keywords in text columns
            if llm:
                for column in columns:
                    keywords = self.keyword_dict.get(column, [])
                    if keywords:  # Only proceed if there are keywords
                        keyword_str = ", ".join(f"'{item}'" for item in keywords)
                        response = chain.invoke({"text": page_text, "keyword": keyword_str}).strip()
                        if response.lower() == 'relevant':
                            self.relevant_pages[column].append(page_num)
            else:
                for column in columns:
                    keywords = self.keyword_dict.get(column, [])
                    if any(keyword.lower() in page_text.lower() for keyword in keywords):
                        self.relevant_pages[column].append(page_num)
            # Check for keywords using LLM
                        
    def parse_llm(self, search: str = None):
    # Define the keys and their corresponding additional data
        parsing_info = {
            'title': None,
            'GLP': None,
            'animal': None,
            'study_date': None,
            'test': None,
            'material': self.parsed_data['title'],
            'guide2': self.keyword_dict.get('guide2'),
            'sdname': self.keyword_dict.get('sdname'),
            'pathologist': self.keyword_dict.get('pathologist'),
            'summary': self.keyword_dict.get('summary'),
            'conclusion': self.keyword_dict.get('conclusion'),
        }

        for key, additional_data in parsing_info.items():
            if search is None or key == search:
                if key in ['material', 'guide2', 'sdname', 'pathologist', 'summary', 'conclusion']:
                    self._parse_generic(key, additional_data)
                else:
                    getattr(self, f'_parse_{key}')()
                    
    def _parse_title(self):

        prompt = PromptTemplate(input_variables=["text"], template=self.prompts['title_lang'])
        # search from the first page
        page_text = get_page(self.doc, 0)  
        chain = prompt | self.llm
        response = chain.invoke({"text": page_text}).strip()
        # post-processing
        self.parsed_data['title'] = response.split('\n')[0].strip().split('Title:')[-1].strip()
        self.parsed_data['id'] = response.split('\n')[1].strip().split('Test Number:')[-1].strip()
        self.parsed_data['lang'] = response.split('\n')[2].strip().split('Language:')[-1].strip()
    
    def _parse_GLP(self):
        if not len(self.relevant_pages["GLP"]):
            self.parsed_data["glpflag"] = "Non-GLP"
            return
            
        text = pages_to_text(self.doc, self.relevant_pages['GLP'])
        glp_flag = self._invoke_chain(text, self.prompts['glp']['glpflag'])
        self.parsed_data["glpflag"] = glp_flag
        
        if glp_flag == "GLP":
            self.parsed_data['guide1'] = self._invoke_chain(text, self.prompts['glp']['guide1'], str(self.keyword_dict["GLP"]))
    
    def _parse_animal(self):
        if not len(self.relevant_pages['animal']):
              return
          
        text = pages_to_text(self.doc, self.relevant_pages['animal'])
        animal = self._invoke_chain(text, self.prompts['animal']['animal'], str(self.parsed_data["title"]))
        self.parsed_data['animal'] = animal
        
        if animal != "none": 
            text += pages_to_text(self.doc, self.relevant_pages['animal_date'])
            self.parsed_data['animal_date'] = self._invoke_chain(text, self.prompts['animal']['animal_date'], str(self.keyword_dict["animal_date"]))
 
            text += pages_to_text(self.doc, self.relevant_pages['path'])
            self.parsed_data['path'] = self._invoke_chain(text, self.prompts['animal']['path'], str(self.parsed_data["title"]))
         
    def _parse_study_date(self):
        
        if not len(self.relevant_pages['study_date']):
            return
        
        text = pages_to_text(self.doc, self.relevant_pages['study_date'])
        study_date = self._invoke_chain(text, self.prompts['study_date'], str(self.keyword_dict["study_date"]))

        dates = ['exam_sdate', 'exam_fdate', 'test_sdate', 'test_fdate']
        date_list = [line.split(": ")[1].strip() for line in study_date.strip().split("\n")]
        for i, date in enumerate(date_list):
            self.parsed_data[dates[i]] = date if date != "none" else "none"
    
    def _parse_test(self):
        
        "utilize: title, summary, conclusion"
        text  = self.parsed_data["summary"] + self.parsed_data["conclusion"] + self.parsed_data["title"]
        self.parsed_data['test_group'] = self._invoke_chain(text, self.prompts['test']['test_group'], str(self.keyword_dict["test_group"]))
        self.parsed_data['test_item'] = self._invoke_chain(text, self.prompts['test']['test_item'])

    def _parse_generic(self, page_key: str, additional_data: str = None):
        # page_key = guide2, sdname, pathologist, summary, conlcusion
        # additional_data: guide2, keyword_dict['guide2], material --> parsed_data['title']
        if not len(self.relevant_pages[page_key]):
            return

        text = pages_to_text(self.doc, self.relevant_pages[page_key])
        result = self._invoke_chain(text, self.prompts[page_key], additional_data)
        self.parsed_data[page_key] = result
                    
    def _invoke_chain(self, text, prompt, keyword=None):
        prompt_template = PromptTemplate.from_template(prompt)
        chain = prompt_template | self.llm
        input_data = {"text": text}
        if keyword:
            input_data["keyword"] = keyword
        result = chain.invoke(input_data).strip()
        
        return result

    def refresh(self):
        self.parsed_data = {column: "none" for column in self.data['column_order']}
        self.relevant_pages = {column: [] for column in self.searching_column}  

    def rag(self, retriever, query):
        
        docs = retriever.invoke(query)
        prompt = PromptTemplate(
            input_variables=["docs", "question"],
            template="""
            Answer the question based only on the following context: {docs}
    
            Question: {question}.  
            """
            )
        
        chain = prompt | self.llm | StrOutputParser()

        response = chain.invoke({'docs': ((docs)), 'question':query})
    
        return response
    
if __name__ == "__main__":
   # model = 'mistral:latest'
    model = 'gemma2:27b'
    btt_parser = Biollm(model= model)
    
    path = "/home/workspace/btt/bttReports/2021/RJ21225-V.pdf"
    btt_parser.run(path)
    print(btt_parser.parsed_data)
    result = btt_parser.run_one(path, search = 'animal_date', llm_search = False)
    print(result)
