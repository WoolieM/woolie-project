from typing import Annotated
from fastapi import FastAPI, Query
from pydantic import BaseModel
from enum import Enum

app = FastAPI()


fake_db = {
    1:  {'name': 'woolie', 'age': 14, 'country': 'Australia'},
    2:  {'name': 'Cassy', 'age': 22, 'country': 'UK'}
}


class EmployeeUpdate(BaseModel):
    name: str
    age: int
    country: str


class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None


class UserPublic(BaseModel):
    username: str
    email: str


class Message(BaseModel):
    message: str


class UserLogin(BaseModel):
    username: str
    password: str


@app.post('/login/{my_login}', response_model=UserPublic | Message)
def login(my_login: str, user_data: UserLogin):
    if my_login == 'yes':
        user_from_db = {
            'username': 'woolie',
            'email': 'woo@woo.woo',
            'test1': 'fake',
            'test2': 'fake2'
        }
        return user_from_db
    else:
        return {"message": "you are wrong"}


@app.get("/employee/{emp_id}")
def get_employee(emp_id: int):
    current_employee = fake_db.get(emp_id)
    return current_employee


@app.get("/employee/aa/{emp_id}")
def get_employee_aa(emp_id: int):
    return fake_db.get(emp_id)


@app.put("/employee/{emp_id}")
def update_employee(emp_id: int, employee: EmployeeUpdate):
    if emp_id in fake_db:
        fake_db[emp_id] = employee.model_dump()

        return {"message": "update good", "newdata": fake_db.get(emp_id)}
    else:
        return {"message": "not found"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.get("/items/")
async def read_items(
    q: Annotated[str | None, Query(
        max_length=10, min_length=1, alias="item-query")] = None
):
    results = {
        'items': [{'item_id': 'Foo'}, {'item_id': 'Bar'}]
    }
    if q:
        results.update({'q': q})
    return results


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {
        "item_name": item.name,
        "item_id": item_id,
        "is_offer": item.is_offer,
        "mytest_aa": item.price,
        "mytest_bb": item.model_dump()
    }


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@app.get("/model/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}
