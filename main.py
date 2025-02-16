
import os
import math
import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv


HH_BASE_URL = "https://api.hh.ru/vacancies"
SJ_BASE_URL = "https://api.superjob.ru/2.0/vacancies/"


def load_env_variable():
    load_dotenv()
    sj_secret_key = os.getenv("SJ_SECRET_KEY")
    if not sj_secret_key:
        raise ValueError("""У Вас нет секретного ключа. Пожалуйста, напишите 
                         Ваш секретный ключ в файл .env""")
    return sj_secret_key


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


def calculate_statistics(vacancies, predict_salary_func):
    salaries = []
    for vacancy in vacancies:
        predicted_salary = predict_salary_func(vacancy)        
        if predicted_salary is not None:
            salaries.append(predicted_salary)
    average_salary = round(sum(salaries) / len(salaries)) if salaries else None
    return average_salary, len(salaries)


def get_hh_statistics(langs, params):
    table_data = [["Язык программирования", "Вакансий найдено",
                   "Вакансий обработано", "Средняя зарплата"]]

    for lang in langs:
        params["text"] = f"Программист {lang}"
        params["page"] = 0

        total_vacancies = 0
        processed_vacancies = 0
        all_vacancies = []

        while True:
            try:
                response = requests.get(HH_BASE_URL, headers={
                                        "Content-Type": "text/plain; charset=UTF-8"}, params=params)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                break

            response_data = response.json()
            vacancies = response_data.get("items", [])
            total_vacancies = response_data.get("found", 0)

            all_vacancies.extend(vacancies)
            if params["page"] >= response_data.get("pages", 1) - 1:
                break
            params["page"] += 1

        average_salary, processed_vacancies = calculate_statistics(
            all_vacancies, predict_rub_salary_hh)
        table_data.append(
            [lang, total_vacancies, processed_vacancies, average_salary])

    return table_data


def get_sj_statistics(langs, params, headers):
    table_data = [["Язык программирования", "Вакансий найдено",
                   "Вакансий обработано", "Средняя зарплата"]]

    for lang in langs:
        params["keyword"] = f"Программист {lang}"
        params["page"] = 0

        total_vacancies = 0
        processed_vacancies = 0
        all_vacancies = []

        while True:
            try:
                response = requests.get(
                    SJ_BASE_URL, headers=headers, params=params)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                break

            response_data = response.json()
            vacancies = response_data.get("objects", [])
            total_vacancies = response_data.get("total", 0)

            all_vacancies.extend(vacancies)
            if not response_data.get("more", False):
                break
            params["page"] += 1

        average_salary, processed_vacancies = calculate_statistics(
            all_vacancies, predict_rub_salary_sj)
        table_data.append(
            [lang, total_vacancies, processed_vacancies, average_salary])

    return table_data


def main():
    sj_secret_key = load_env_variable()

    programming_languages = ["PHP", "Python", "Java",
                             "JavaScript", "C++", "C#", "C", "Ruby", "Scala", "Go"]
    moscow_area_id = 1
    moscow_town_id = 4
    vacancies_per_page = 100

    hh_params = {"area": moscow_area_id, "per_page": vacancies_per_page}
    sj_params = {"town": moscow_town_id, "count": vacancies_per_page}

    sj_headers = {"X-Api-App-Id": sj_secret_key}

    hh_statistics = get_hh_statistics(programming_languages, hh_params)
    sj_statistics = get_sj_statistics(
        programming_languages, sj_params, sj_headers)

    print(AsciiTable(hh_statistics, "HeadHunter").table)
    print(AsciiTable(sj_statistics, "SuperJob").table)


if __name__ == "__main__":
    main()
