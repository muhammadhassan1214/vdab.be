# python
import os
import re
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import get_output_file_name, get_normal_driver, check_element_visibility_and_return_text, check_element_visibility_and_return_href, create_xpath_1, shorten_vdab_url


def _wait_for_count_change(driver, selector, prev, timeout=15) -> int:
    def _changed(d):
        text = check_element_visibility_and_return_text(d, selector)
        count = _to_int(text)
        return count if count != prev else None
    return WebDriverWait(driver, timeout).until(_changed)

def _to_int(text: str) -> int:
    m = re.search(r'\d+', text or '')
    return int(m.group()) if m else 0

def _read_done_set(path: str = 'done.txt') -> set[str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def _click_next(driver, timeout: int = 10) -> bool:
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "(//span[text()= 'Volgende']/parent::vdab-button)[1]"))
        )
        btn.click()
        return True
    except Exception:
        return False

def main():
    query = input("\nEnter the VDAB search query URL: ").strip()
    if not query.startswith('https://www.vdab.be/vindeenjob/vacatures'):
        print("Invalid VDAB search query URL. Please provide a valid URL.")
        return
    output_file_name = get_output_file_name(query)
    driver = get_normal_driver()
    page_count, loop_count = 1, 1

    try:
        done_urls = _read_done_set('done.txt')

        driver.get(query)
        WebDriverWait(driver, 40).until(
            EC.visibility_of_element_located((By.XPATH, "//h4[@class= 'c-vacature__content-title']/child::a[1]"))
        )
        total_jobs_txt = check_element_visibility_and_return_text(
            driver, (By.XPATH, "//div[contains(@class, 'c-results__jobs')]/strong")
        )
        total_jobs = _to_int(total_jobs_txt)

        # Open first job
        driver.find_element(By.XPATH, "//h4[@class= 'c-vacature__content-title']/child::a[1]").click()

        current_job_count_selector = (By.XPATH, "(//div[@class= 'c-pagination']/div/strong)[1]")
        current_job_count = _to_int(check_element_visibility_and_return_text(driver, current_job_count_selector))

        while current_job_count <= total_jobs and total_jobs > 0:
            # Per-vacancy try/except so one failure doesn't stop everything
            try:
                url = shorten_vdab_url(driver.current_url)
                vdab_vacancy_number = url.split('/')[-1]

                if vdab_vacancy_number in done_urls:
                    if not _click_next(driver):
                        break
                    prev = current_job_count
                    current_job_count = _wait_for_count_change(driver, current_job_count_selector, prev, 15)
                    if loop_count == 15:
                        print(f"Page {page_count} processed successfully.")
                        page_count, loop_count = page_count + 1, 0
                    loop_count += 1
                    continue

                job_title = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//h1[contains(@class, 'vej__detail-vacature-title')]")
                )
                job_region = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//div[@class= 'c-job-info-main__location']/span[last()]")
                )

                online_since_1 = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//div[contains(@class, 'c-job-info-main__date')][1]")
                )
                if 'Online sinds:' in (online_since_1 or ''):
                    online_since_1 = online_since_1.split(': ', 1)[-1].strip()

                last_modified = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//div[contains(@class, 'c-job-info-main__date')][2]")
                )
                if 'Gewijzigd sinds:' in (last_modified or ''):
                    last_modified = last_modified.split(': ', 1)[-1].strip()

                contract_types = [el.text for el in driver.find_elements(By.XPATH, create_xpath_1('Contract'))]
                required_studies_text = [el.text for el in driver.find_elements(By.XPATH, create_xpath_1('Vereiste studies'))]
                required_experience_text = [el.text for el in driver.find_elements(By.XPATH, create_xpath_1('Werkervaring'))]
                languages_text = [el.text for el in driver.find_elements(By.XPATH, create_xpath_1('Talenkennis'))]

                company_name_txt = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//div[@class= 'vej-results__companymeta']/h4")
                )
                company_url = check_element_visibility_and_return_href(
                    driver, (By.XPATH, "//h5[text()= 'Bedrijfswebsite']/following-sibling::div/a")
                )
                job_description = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//h3[text()= 'Functieomschrijving']/following-sibling::p")
                )
                profile = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//h3[text()= 'Profiel']/following-sibling::p")
                )
                professional_skills = [
                    el.text for el in driver.find_elements(By.XPATH, "//h3[text()= 'Professionele vaardigheden']/following-sibling::div/ul/li")
                ]
                place_of_employment = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//h3[contains(text(), 'Plaats tewerkstelling')]/parent::div/following-sibling::p")
                )
                company_mail = check_element_visibility_and_return_text(driver, (By.ID, "vej_sollicitatieEmailadres"))
                company_phone = check_element_visibility_and_return_text(driver, (By.ID, "vej_sollicitatieTelefoonnummer"))
                other_jobs_by_the_company = check_element_visibility_and_return_href(driver, (By.ID, "vej-bedrijf-logo"))
                offer = check_element_visibility_and_return_text(driver, (By.XPATH, "//h3[text()= 'Aanbod']/following-sibling::p"))
                vdab_profession = check_element_visibility_and_return_text(driver, (By.ID, 'vej_c2_beroepsTitel')).split(': ')[-1].strip()

                online_since_2 = check_element_visibility_and_return_text(
                    driver, (By.XPATH, "//p[contains(text(), 'Online sinds:')]/span")
                )  # already the numeric span; no split needed

                # Related results with clearer loop vars
                rel_title_els = driver.find_elements(By.XPATH, "//h4[@class= 'c-vacature__content-title u-hyphenate']/a")
                rel_company_els = driver.find_elements(By.XPATH, "//div[@class= 'c-vacature-meta__location']/span/strong[1]")
                rel_location_els = driver.find_elements(By.XPATH, "//div[@class= 'c-vacature-meta__location']/span/strong[2]")
                related_results_titles = [f"Job Title: {el.text}" for el in rel_title_els]
                related_results_company_names = [f"Company: {el.text}" for el in rel_company_els]
                related_results_locations = [f"Location: {el.text}" for el in rel_location_els]
                related_results = list(zip(related_results_titles, related_results_company_names, related_results_locations))

                data = {
                    'Search Query': query,
                    'Page Number': page_count,
                    'Job URL': url,
                    'Job Title': job_title,
                    'Job Region': job_region,
                    'Online Since': online_since_1,
                    'Last Modified': last_modified,
                    'Contract Types': contract_types,
                    'Required Studies': required_studies_text,
                    'Required Experience': required_experience_text,
                    'Languages': languages_text,
                    'Company Name': company_name_txt,
                    'Company Mail': company_mail,
                    'Company Phone': company_phone,
                    'Company URL': company_url,
                    'Job Description': job_description,
                    'Profile': profile,
                    'Professional Skills': professional_skills,
                    'Place of Employment': place_of_employment,
                    'Offer': offer,
                    'VDAB Vacancy Number': vdab_vacancy_number,
                    'VDAB Profession': vdab_profession,
                    'Online Since (Numeric)': online_since_2,
                    'Other Jobs by the Company': other_jobs_by_the_company,
                    'Related Results': related_results
                }

                df = pd.DataFrame([data])
                if not os.path.exists(output_file_name):
                    df.to_csv(output_file_name, mode='w', header=True, index=False, encoding='utf-8-sig', lineterminator='\n')
                else:
                    df.to_csv(output_file_name, mode='a', header=False, index=False, encoding='utf-8-sig', lineterminator='\n')

                print(f"Data for {job_title} saved successfully.")
                with open('done.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{vdab_vacancy_number}\n")
                done_urls.add(vdab_vacancy_number)

            except Exception as job_err:
                print(f"Skipping due to error: {job_err}")

            # Move to next vacancy
            prev = current_job_count
            if not _click_next(driver):
                break
            try:
                current_job_count = _wait_for_count_change(driver, current_job_count_selector, prev, 15)
            except Exception:
                break

            if loop_count == 15:
                print(f"Page {page_count} processed successfully.")
                page_count, loop_count = page_count + 1, 0
            loop_count += 1

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
