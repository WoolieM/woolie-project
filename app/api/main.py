from typing import Annotated, Literal
from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, AfterValidator, Field
from enum import Enum
import random
app = FastAPI()


fake_db = {
    1:  {'name': 'woolie', 'age': 14, 'country': 'Australia'},
    2:  {'name': 'Cassy', 'age': 22, 'country': 'UK'}
}

data_1 = {
    "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
    "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
    "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2"
}


def check_valid_id(id: str):
    if not id.startswith(('isbn-', 'imdb-')):
        raise ValueError('Invalid ID format, abc')
    return id


class EmployeeUpdate(BaseModel):
    name: str
    age: int
    country: str


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


@app.get("/items_aa/{item_id}")
async def read_item_aa(
        item_id: str,
        q: str,
        short: bool = False

):
    item = {'item_id': item_id}
    if q:
        item.update({'q': q})
    if not short:
        item.update(
            {'description': 'This sucks'}
        )
    return item


@app.get("/items/")
async def read_items(
    q: Annotated[
        list[str] | None,
        Query(
            title='i am too awesome woolie',
            description='everyting is going to be okay',
            max_length=10,
            min_length=3,
            alias="item-query",
            deprecated=True
        )
    ] = ['my_defualt_1', 'my_defualt_2', 'my_defualt_3']
):
    results = {
        'items': [{'item_id': 'Foo'}, {'item_id': 'Bar'}]
    }
    if q:
        results.update({'q': q})
    return results


@app.get("/items_2/")
async def read_items_2(
    id: Annotated[
        str | None,
        AfterValidator(check_valid_id)
    ] = None
):
    if id:
        item = data_1.get(id)
    else:
        id, item = random.choice(list(data_1.items()))
    return {'id': id, 'name': item}


class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None
    description: str | None = None
    tax: float | None = None


class User2(BaseModel):
    username: str
    full_name: str | None = None


@app.put("/items/{item_id}")
async def update_item(
    item_id: Annotated[
        int,
        Path(
            title='The ID of the item to get my woolie',
            ge=0,
            le=10
        )
    ],
    user: User2,
    item: Annotated[Item, Body(embed=True)],
    importance: Annotated[int, Body(gt=0)],
    q: str | None = None
):
    results = {
        'item_id_up': item_id,
        'item woolie': item,
        'user': user,
        'importantce my woolie': importance
    }
    if q:
        results.update({'q woolie': q})
    return results


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


@app.post('/item/')
async def create_item(item: Item):
    item_dict = item.model_dump()
    price_with_tax = item.price

    if item.tax is not None:
        price_with_tax = item.price + item.tax

    item_dict.update({'price and tax': price_with_tax})
    return item_dict


@app.get('/items_3/{item_id}')
async def read_items_3(
    item_id: Annotated[
        int,
        Path(title='The ID of the item to get Wooliter', ge=3)
    ],
    q: Annotated[
        str | None,
        Query(alias='item-query')
    ],
    size: Annotated[
        float,
        Query(
            gt=0,
            lt=10.5,
            description='just put float',
            alias='float-query-abwoo'

        )
    ]
):
    resutls = {'item_id': item_id}
    if q:
        resutls.update({'q': q})
    if size:
        resutls.update({'size': size})
    return resutls


class FilterParams(BaseModel):
    model_config = {'extra': 'forbid'}

    limit: int = Field(14, gt=0, lt=100)
    offset: int = Field(0, ge=0)
    orfer_by: Literal['created_at', 'updated_at'] = 'created_at'
    tags: list[str] = []


@app.get('/items_4/')
async def read_items_4(
    filter_query: Annotated[
        FilterParams,
        Query()
    ]
):
    return filter_query
