def greet():
    print("Hello World")


def search_documents(query):
    return ["doc1","doc2","doc3"]


def validate_response(response):
    pass


def generate_answer(context):
    pass

def search_drug(drug_name):
    print(f"Search for {drug_name}")

def add(a,b):
    return a+b

def calculate_salary(
        salary,
        bonus = 5000
        ):
    return salary*bonus

def add_numbers(*args):
    return sum(args)

def calculate_total(*numbers):
    return sum(numbers)

def create_user(**kwargs):
    print(kwargs)

create_user(
    name = "Chaitanya",
    city = "Hyderabad"
)    

print(calculate_total(10,20,30,40))

print(add_numbers(1,2,3))

total_salary = calculate_salary(10000, 10000)
print(f"Total Salary: {total_salary}")

greet()
#print(search_documents.__name__)
documents = search_documents("WEGOVY")
print(documents)
print(validate_response.__name__)
print(generate_answer.__name__)
search_drug("WEGOVY")
result = add(10,20)
print(result)