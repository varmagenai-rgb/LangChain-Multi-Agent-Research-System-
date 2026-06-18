# class Student:
#     pass

# student1 = Student()
# student2 = Student()

# class Car:
#     pass

# car1 = Car()
# car2 = Car()

# print(student1)
# print(student2)
# print(car1)
# print(car2)

# class Employee:

#     def __init__(self):
#         print(f"Employee Created")

# emp = Employee()

# class AzureSearchService:

#     def __init__(self):
#         print(f"Connecting Azure Serch")

# search = AzureSearchService()

# class OpenAIService:
#     def __init__(self, api_key):
#         self.api_key = api_key

# service = OpenAIService(
#     api_key="xyz"
# )

# print(service.api_key)

# class SearchAgent:
#     def __init__(self, source):
#         self.source = source

# fda = SearchAgent("FDA")
# ema = SearchAgent("EMA")

# print(fda.source)
# print(ema.source)

# class Product:
#     def __init__(self,name, price):
#         self.name = name
#         self.price = price

# product = Product(
#     "Laptop",
#     50000
# )

# print(product.name)
# print(product.price)

# class SearchAgent:
#     def search(self,query):
#         return f"Searching {query}"
    
# agent = SearchAgent()
# print(agent.search("Wegovy"))


# class SearchAgent:
#     def __init__(self, source):
#         self.source = source
    
#     def search(self,query):
#         return f"Searching {query}, source {self.source}"
    
# agent  =  SearchAgent("FDA")
# print(
#     agent.search("Wegovy")
# )


# class Animal:
#     def speak(self):
#         print("Animal Sound")

# class Dog(Animal):
#     pass

# dog = Dog()
# dog.speak()

class BaseAgent():
    def log(self):
        print("logging")

class FdaAgent(BaseAgent):
    pass

class EmaAgent(BaseAgent):
    pass

fdaAgent = FdaAgent()
fdaAgent.log()

emaAgent = EmaAgent()
emaAgent.log()

