import os
import math
import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv


HH_BASE_URL = "https://api.hh.ru/vacancies"
SJ_BASE_URL = "https://api.superjob.ru/2.0/vacancies/"
SJ_SECRET_KEY = os.getenv("SJ_SECRET_KEY")

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


def get_statistics(vacancies, predict_salary_func):
    total_salary = 0
    salary_count = 0

    for vacancy in vacancies:
        salary = predict_salary_func(vacancy)
        if salary:
            total_salary += salary
            salary_count += 1

    if salary_count > 0:
        average_salary = round(
            total_salary / salary_count)
    else:
        None
    return average_salary, len(vacancies)


def get_hh_statistics(langs, params):
    table_data = [["Язык программирования", "Вакансий найдено",
                   "Вакансий обработано", "Средняя зарплата"]]

    for lang in langs:
        params["text"] = f"Программист {lang}"
        page = 0
        total_vacancies = 0
        processed_vacancies = 0

        while True:
            params["page"] = page
            try:
                response = requests.get(
                    HH_BASE_URL, headers=HH_HEADERS, params=params)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                break

            vacancies = response.json()
            vacancy = vacancies.get("items")
            if not vacancy:
                break

            average_salary, count = get_statistics(
                vacancy, predict_rub_salary_hh)
            total_vacancies = vacancies.get("found", 0)
            processed_vacancies += count

            if page >= vacancies.get("pages", 1) - 1:
                break

            page += 1

        table_data.append(
            [lang, total_vacancies, processed_vacancies, average_salary])

    return table_data


def get_sj_statistics(langs, params):
    table_data = [["Язык программирования", "Вакансий найдено",
                   "Вакансий обработано", "Средняя зарплата"]]

    for lang in langs:
        params["keyword"] = f"Программист {lang}"
        page = 0
        total_vacancies = 0
        processed_vacancies = 0

        while page < 10:
            params["page"] = page
            try:
                response = requests.get(
                    SJ_BASE_URL, headers=SJ_HEADERS, params=params)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                break

            vacancies = response.json()
            vacancy = vacancies.get("objects")
            if not vacancy:
                break

            average_salary, count = get_statistics(
                vacancy, predict_rub_salary_sj)
            total_vacancies = vacancies.get("total", 0)
            processed_vacancies += count

            if not vacancies.get("more", False):
                break

            page += 1

        table_data.append(
            [lang, total_vacancies, processed_vacancies, average_salary])

    return table_data


def main():
    load_dotenv()

    langs = ["PHP", "Python", "Java", "JavaScript",
             "C++", "C#", "C", "Ruby", "Scala", "Go"]
    MOSCOW_ID = [1, 4]
    REQUESTS_PER_PAGE = 100

    hh_params = {"area": MOSCOW_ID[0], "per_page": REQUESTS_PER_PAGE}
    sj_params = {"town": MOSCOW_ID[1], "count": REQUESTS_PER_PAGE}

    hh_statistics = get_hh_statistics(langs, hh_params)
    sj_statistics = get_sj_statistics(langs, sj_params)

    print(AsciiTable(hh_statistics, "HeadHunter").table)
    print(AsciiTable(sj_statistics, "SuperJob").table)


if __name__ == "__main__":
    main()
