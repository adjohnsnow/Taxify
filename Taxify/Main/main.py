# import tabula
import numpy as np
import pandas as pd
import os
import re,string
import sys
from dateutil.parser import parse
import spacy
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

import pdfplumber
import pandas as pd



def load_financial_data(pdf_file_path):
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            df_list = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    # Set the first row as column names
                    df = pd.DataFrame(table[1:], columns=table[0])

                    # Check if the DataFrame has more than 6 columns
                    if df.shape[1] > 6:
                        # Drop the last column if it has more than 6 columns
                        df = df.iloc[:, :-1]

                    # Append the DataFrame to the list
                    df_list.append(df)
    except Exception as e:
        print('The Error is', e)
        df_list = []

    # Concatenate individual DataFrames into one
    df_fin = pd.concat(df_list, axis=0, ignore_index=True)

    # Clean up column names (convert to strings and remove leading/trailing whitespaces)
    df_fin.columns = df_fin.columns.astype(str).str.strip()

    # Remove rows containing "Date" in the first column
    df_fin = df_fin[~df_fin.iloc[:, 0].astype(str).str.contains("Date")]

    # Convert 'Date' column to datetime if it exists
    if 'Date' in df_fin.columns:
        df_fin['Date'] = pd.to_datetime(df_fin['Date'])

    df_fin.rename(columns={
        'Transaction Date': 'Date',
        'Transaction Remarks': 'Transaction',
        'Transaction\nRemarks': 'Transaction',
        'Transaction\nDate': 'Date',
        'Withdrawal\nAmount ( )': 'Withdrawal',
        'Deposit Amount\n( )': 'Deposit',
        'Sr no.': 'S No.',
        'Value\nDate': 'Value Date'
    }, inplace=True)

    df_fin['Withdrawal'] = pd.to_numeric(df_fin['Withdrawal'])
    df_fin['Deposit'] = pd.to_numeric(df_fin['Deposit'])

    df_fin['Deposit'] = df_fin['Deposit'].fillna(0)
    df_fin['Withdrawal'] = df_fin['Withdrawal'].fillna(0)

    df_fin['Net_Amount'] = df_fin['Deposit'] - df_fin['Withdrawal']

    return df_fin

def process_data(df_fin): #sare function yha se call
  # Apply the function to the 'Transaction' column
  df_fin = df_fin[~df_fin['Transaction'].str.contains('UPI')]
  df_fin['Salary/Withdrawal'] = df_fin['Transaction'].apply(rename_transaction)
  # Apply the function to the 'Transaction' column
  df_fin['Loan'] = df_fin['Transaction'].apply(categorize_loan_type)
  # Apply the function to the 'Transaction' column
  df_fin['School Fees'] = df_fin['Transaction'].apply(categorize_school_fees)
  # Apply the function to the 'Transaction' column
  df_fin['Recipient Name'] = df_fin['Transaction'].apply(extract_name)
  df_fin['rent'] = df_fin['Transaction'].apply(categorize_rent_payment)
  # Apply the function to the 'Transaction' column
  df_fin['Service'] = df_fin['Transaction'].apply(extract_service)
  df_fin['BIL'] = df_fin['Transaction'].apply(extract_term_from_bil)
  df_fin['Card'] = df_fin['Transaction'].apply(extract_service)
  df_fin.fillna('', inplace=True)
  df_fin['Results'] = df_fin['rent'] + df_fin['Recipient Name'] + df_fin['School Fees'] + df_fin['Loan'] + df_fin['Salary/Withdrawal'] + df_fin['Service'] +df_fin['BIL']
  df_fin['Results'] = df_fin.apply(lambda row: row['Transaction'] if row['Results'] == '' else row['Results'], axis=1)
  df_fin['Results'] = df_fin['Results'].str.lower()
  return df_fin



def rename_transaction(transaction):

    # Define a function to rename the transaction based on the pattern
    transaction = transaction.lower()  # Convert to lowercase
    if re.match(r'^at[wl]/', transaction) or "cash withdrawal" in transaction or re.match(r'^atm wdl-', transaction):
        return 'ATM_Withdrawals'
    elif re.match(r'^salary-', transaction) or re.match(r'salary', transaction) or re.match(r'freelance work', transaction):
        return 'Salary'
    else:
        return None


# Function to categorize loan types
def categorize_loan_type(transaction):
    loan_categories = {
    'Personal_Loan': ['personal loan'],
    'Car_Loan': ['car loan'],
    'Home_Loan': ['home loan', 'mortgage'],
    'Student_Loan': ['student loan'],
    'Business_Loan': ['business loan']}

    transaction_lower = transaction.lower()
    for category, keywords in loan_categories.items():
        if any(keyword in transaction_lower for keyword in keywords):
            return category
    return None



# Function to categorize school fees transactions
def categorize_school_fees(transaction):
    school_fees_keywords = ['school fee', 'tuition fee', 'college fee','PG fee']
    transaction_lower = transaction.lower()
    if any(keyword in transaction_lower for keyword in school_fees_keywords):
        return 'Education_Fees'
    return None



def extract_name(transaction):
    match = re.search(r'Fund\nTransfer\s*/\s*(\S.*)$', transaction)
    if match:
        return match.group(1)
    return None



# Function to categorize rent payment transactions
def categorize_rent_payment(transaction):
    rent_keywords = ['rent', 'property management', 'tenant', 'lease']
    transaction_lower = transaction.lower()
    if any(keyword in transaction_lower for keyword in rent_keywords):
        return 'Rent'
    return None



# Function to extract service name
def extract_service(transaction):
    pattern = re.compile(r'VSI/([A-Z]+)')
    match = re.search(pattern, transaction)
    if match:
        return match.group(1)
    return None



def extract_term_from_bil(transaction):
    match = re.search(r'BIL/[^/]+/[^/]+/([^/]+)', transaction)
    if match:
        return match.group(1)
    return None





# Function to extract service name
def extract_service(transaction):
    pattern = re.compile(r'VPS/([A-Z]+)')
    match = re.search(pattern, transaction)
    if match:
        return match.group(1)
    return None






# Function to apply NLP and store the output as a dictionary
def apply_nlp(row):
    nlp = spacy.load("en_core_web_sm")
    category_mapping = {
    "life_insurance": ["max life insurance", "birla life insurance", "other life insurance aliases"],
    "education_fees": [ "P.s. Prahlad Garhi", "U.p.s. Raispur (girls)", "U.p.s.sudama Puri", "p.s.pasonda -2", "A.m.u. Public School", "A.p.n. Public School", "A.p.s. Public Jr.h. School", "A.r. Public School", "Aamarpali Pub. School", "Adarh Bal Vidya Mandir",
    "Adars Kinder Garden Pub Jr.h.school", "Adarsh (rds) Public School", "Adarsh Jr. High School", "Adarsh Public School", "Adarsh Public School", "Adarsh Public School", "Adarsh Vidyalay", "Advance Public School Pratap Vihar", "Amar Jyoti Pub. School", "Anamika Vidya Pub. School",
    "Anand Tranning Centre For Mentally Related Children Nandgram", "Angels Public School", "Army Indian Public School", "Arpan Public School Ghookna", "Arunoday Convent School", "Arwachin Public School", "Arya Public School,karkar Mada", "Aryan Acedamy Jr.h. School", "Asha Vidyalay For Deaf", "Ashwani Public School",
    "Asian Public School", "Astha Jr.h. School", "Astha Public School", "Astha Public School", "Avishkar The School Nandgram Ghaziabad", "Avn. International School", "B.k. Shisu Mandir Jr.h. School", "B.p. Jr. H. School", "B.p.s. Ambedkar Nagar", "B.p.s. Bajaria",
    "B.p.s. Bhovapur", "B.p.s. Kala General", "B.p.s. Krishian Nagar Bagu", "B.p.s. Nasirpur -i", "B.p.s. Pappu Colony", "B.p.s. Patel Marg", "B.p.s. Raj Nagar", "B.p.s. Saddik Nagar Sihani-i", "B.p.s. Sarai Hindustani", "B.p.s. Shyam Park",
    "B.p.s. Sihani -ii", "B.p.s. Subhash Nagar", "B.p.s. Sudama Puri", "B.p.s.govind Puram", "B.p.s.sarai Nazar Ali", "B.s.r. Public School", "Bab Bhragu Nath Jr H. School", "Babu Lal Jr. H School", "Baby Moral School", "Bahrat Public School",
    "Bal Bharti Public School", "Bal Gopal Siksha Niketan", "Bal Gyan Public School", "Bal Jagat Inter Coll Sikh Road", "Bal Shiksha School", "Bal Vasundhra Shiksha Sadan", "Bal Vidya Kendr", "Bal Vidya Mandir", "Bal Vikas Public School", "Bal Vikas S. S. Pub. School",
    "Balendra Shiksha Kendra", "Ben-hur Public School", "Bhadwaj Siksha Niketan", "Bhagat Nanu Public School", "Bhagirath Seva Sansthan", "Bhagwan Das Pub. School", "Bharadwaj Pub. J.h. School", "Bharat Public School", "Bharti Shiksha Bhawan,maliwada", "Bhartiya Vidya Mandir"],
    "home_loan": ["abc loan corp", "xyz loan company", "other loan company aliases"],
    "health_insurance":["National Insurance Answer", "Go Digit General Insurance", "Bajaj Allianz General Insurance Answer",
    "Cholamandalam MS General Insurance Answer", "Bharti AXA General Insurance Answer", "HDFC ERGO General Insurance Answer",
    "Future Generali India Insurance Answer", "The New India Assurance Answer", "Iffco Tokio General Insurance Answer",
    "Reliance General Insurance Answer", "Royal Sundaram General Insurance Answer", "The Oriental Insurance Answer",
    "Tata AIG General Insurance Answer", "SBI General Insurance Answer", "Acko General Insurance", "Navi General Insurance",
    "Zuno General Insurance (formerly known as Edelweiss General Insurance)", "ICICI Lombard General Insurance Answer",
    "Kotak Mahindra General Insurance Answer", "Liberty General Insurance", "Magma HDI General Insurance Answer",
    "Raheja QBE General Insurance Answer", "Raheja QBE General Insurance Answer", "Shriram General Insurance Answer",
    "United India Insurance Answer", "Manipal Cigna Health Insurance Company Limited", "Aditya Birla Health Insurance Answer",
    "Star Health & Allied Insurance Answer", "MAX Bupa Health Insurance Company", "Care Health Insurance",
    "Universal Sompo General Insurance Answer", "Kotak Mahindra Life Insurance", "Universal Sompo General Insurance (Life and Health)",
    "Religare Health Insurance", "HDFC Life Insurance", "Bharti AXA Life Insurance", "Aviva Life Insurance",
    "PNB MetLife India Insurance", "Canara HSBC Oriental Bank of Commerce Life Insurance",
    "Star Union Dai-ichi Life Insurance", "IndiaFirst Life Insurance", "Bajaj Allianz Life Insurance",
    "ICICI Prudential Life Insurance", "Max Life Insurance", "LIC", "DHFL General Insurance",  "Company name",
    "National Insurance Answer"]
}

    taxable_entities = ["education_fees" , "home_loan" , "salary" ,"rent" , "life_insurance"]
    transaction = row['Results']
    net_amount = row['Net_Amount']
    doc = nlp(transaction)

    for category, aliases in category_mapping.items():
        for alias in aliases:
            if alias.lower() in transaction:
                transaction = transaction.replace(alias.lower(), category.lower())

    # Extract named entities and corresponding values
    named_entities = {ent.text: net_amount for ent in doc if ent.text in taxable_entities}

    return named_entities




def calculate_mutual_funds(investment_amount):
    # Corresponds to Section 80C
    limit = 150000
    return min(investment_amount, limit)

def calculate_health_insurance(self_insurance, parent_insurance, is_senior):
    # Corresponds to Section 80D
    base_limit = 25000
    additional_limit = 50000 if is_senior else 25000
    return min(self_insurance, base_limit) + min(parent_insurance, additional_limit)

def calculate_education_loan(interest_amount):
    # Corresponds to Section 80E
    return interest_amount

def calculate_savings_account_interest(interest_income):
    # Corresponds to Section 80TTA
    limit = 10000
    return min(interest_income, limit)

def calculate_donations(donation_amount):
    # Corresponds to Section 80G
    return donation_amount

def calculate_home_loan_interest(home_loan_interest):
    # Corresponds to Section 24(b)
    limit = 200000
    return min(home_loan_interest, limit)

def calculate_rent_paid(rent_paid, salary):
    # Corresponds to Section 80GG
    return min(rent_paid, 5000 * 12)  # Assuming a monthly limit of 5000

def calculate_nps_contribution(nps_contribution):
    # Corresponds to Section 80CCD(1B)
    limit = 50000
    return min(nps_contribution, limit)

def calculate_disability(disability_amount, severe_disability):
    # Corresponds to Section 80U
    limit = 125000 if severe_disability else 75000
    return min(disability_amount, limit)

def calculate_hra(hra_received, rent_paid, basic_salary):
    # Corresponds to House Rent Allowance
    return min(hra_received, rent_paid - 0.1 * basic_salary)

def process_deductions(deductions):
    calculated_deductions = {}
    for category, data in deductions.items():
        data = abs(data)
        if category == "mutual_funds":
            calculated_deductions[category] = calculate_mutual_funds(data)
        elif category == "health_insurance":
            self_insurance, parent_insurance, is_senior = data
            calculated_deductions[category] = calculate_health_insurance(self_insurance, parent_insurance, is_senior)
        elif category == "education_loan":
            calculated_deductions[category] = calculate_education_loan(data)
        elif category == "Savings Account Interest":
            calculated_deductions[category] = calculate_savings_account_interest(data)
        elif category == "donations":
            calculated_deductions[category] = calculate_donations(data)
        elif category == "home_loan":
            calculated_deductions[category] = calculate_home_loan_interest(data)
        elif category == "rent":
            salary = deductions["salary"]
            calculated_deductions[category] = calculate_rent_paid(data, salary)
        elif category == "nps_contribution":
            calculated_deductions[category] = calculate_nps_contribution(data)
        elif category == "disability":
            disability_amount, severe_disability = data
            calculated_deductions[category] = calculate_disability(disability_amount, severe_disability)
        elif category == "hra":
            hra_received, rent_paid, basic_salary = data
            calculated_deductions[category] = calculate_hra(hra_received, rent_paid, basic_salary)
        # Additional categories can be added here

    return calculated_deductions


def calculate(amount, percent):
    return (amount * percent) / 100

def calculate_income_tax(total_income):

    if total_income <= 250000:
        tax = 0
    elif total_income <= 500000:
        tax = calculate(total_income - 250000, 5)
    elif total_income <= 1000000:
        tax = calculate(250000, 5) + calculate(total_income - 500000, 20)
    else:  # for income above 10 lakhs
        tax = calculate(250000, 5) + calculate(500000, 20) + calculate(total_income - 1000000, 30)

    # Adding 4% Health and Education Cess to the tax
    cess = calculate(tax, 4)
    total_tax_including_cess = tax + cess

    if total_income<500000:
      return 0
    return total_tax_including_cess

def main(pdf_file_path):
    df_fin = load_financial_data(pdf_file_path)
    df_fin = process_data(df_fin)

    df_fin['NLP_Output'] = df_fin.apply(apply_nlp, axis=1)

    result_dict = {}
    for d in df_fin['NLP_Output']:
        for key, value in d.items():
            if key in result_dict:
                result_dict[key] += value
            else:
                result_dict[key] = value


    calculated_deductions = process_deductions(result_dict)

    total_calculated_deductions = sum(calculated_deductions.values())
    net_income = result_dict["salary"] - total_calculated_deductions
    tax_including_cess = int(calculate_income_tax(net_income))
    return tax_including_cess

if __name__ == "__main__":
    pdf_file_path = r"C:\\Users\\sjsah\\OneDrive\\Desktop\\modified_balance_sheet.pdf"
    main(pdf_file_path)