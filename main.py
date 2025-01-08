import os
import math
import requests
from terminaltables import AsciiTable

from dotenv import load_dotenv
load_dotenv()

HH_BASE_URL = "https://api.hh.ru/vacancies"
SJ_BASE_URL = "https://api.superjob.ru/2.0/vacancies/"
SJ_SECRET_KEY = os.getenv("SECRET_KEY")

SJ_HEADERS = {
    "X-Api-App-Id": SJ_SECRET_KEY
}

HH_HEADERS = {
    "Content-Type": "text/plain; charset=UTF-8"
}

def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None

def predict_rub_salary_hh(vacancy):
    salary = vacancy.get("salary")
    if salary and salary["currency"] == "RUR":
        return predict_salary(salary.get("from"), salary.get("to"))
    return None

def predict_rub_salary_sj(vacancy):
    if vacancy.get("currency") == "rub":
        return predict_salary(vacancy.get("payment_from"), vacancy.get("payment_to"))
    return None

def get_vacancy_statistics(base_url, headers, params, langs, predict_salary_func):
    TABLE_DATA = [
        ["Язык программирования", "Вакансий найдено",
            "Вакансий обработано", "Средняя зарплата"],
    ]
    statistics = {}

    for lang in langs:
        params["keyword" if "superjob" in base_url else "text"] = f"Программист {lang}"

        page = 0
        total_salary = 0
        salary_count = 0
        processed_vacancies = 0

        while True:
            params["page"] = page
            try:
                response = requests.get(
                    base_url, headers=headers, params=params)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                break

            vacancies = response.json()
            items = vacancies.get(
                "items" if "hh.ru" in base_url else "objects", [])

            if not items:
                break

            for vacancy in items:
                salary = predict_salary_func(vacancy)
                if salary:
                    total_salary += salary
                    salary_count += 1
                processed_vacancies += 1

            total_vacancies = vacancies.get("found", len(items))
            max_page = math.ceil(total_vacancies / params.get("per_page", 100))

            if page >= max_page - 1:
                break

            page += 1

        average_salary = round(
            total_salary / salary_count) if salary_count > 0 else None
        statistics[lang] = {
            "vacancies_found": total_vacancies,
            "vacancies_processed": processed_vacancies,
            "average_salary": average_salary,
        }
        TABLE_DATA.append(
            [lang, total_vacancies, processed_vacancies, average_salary])

    return TABLE_DATA



langs = ["PHP", "Python", "Java", "JavaScript",
         "C++", "C#", "C", "Ruby", "Scala", "Go"]


hh_params = {
    "area": 1,  
    "per_page": 100,
}
hh_statistics = get_vacancy_statistics(
    HH_BASE_URL, HH_HEADERS, hh_params, langs, predict_rub_salary_hh)


sj_params = {
    "town": 4,  
    "count": 100,
}
sj_statistics = get_vacancy_statistics(
    SJ_BASE_URL, SJ_HEADERS, sj_params, langs, predict_rub_salary_sj)


title_of_table_sj = f"SuperJob {sj_params['town']}"

table_instance_sj = AsciiTable(sj_statistics, title_of_table_sj)
table_instance_sj.justify_columns[2] = 'right'
print(table_instance_sj.table)


title_of_table_hh = f"HeadHunter {hh_params['area']}"
table_instance_hh = AsciiTable(hh_statistics, title_of_table_hh)
table_instance_hh.justify_columns[2] = 'right'
print(table_instance_hh.table)
