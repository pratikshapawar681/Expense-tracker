from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import Base, engine, SessionLocal
from models import User, Expense, Budget
from schemas import (
    UserCreate,
    UserLogin,
    ExpenseCreate,
    ExpenseUpdate,
    BudgetCreate,
    BudgetUpdate
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    get_current_user_email
)

from routes.report_routes import router as report_router


app = FastAPI(title="Expense Tracker API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://expensetrackerfrontend-p4ei.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

app.include_router(report_router)


security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/")
def home():
    return {
        "message": "Expense Tracker API Running"
    }


# ---------------- REGISTER ----------------

@app.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing = db.query(User).filter(
        User.email == user.email
    ).first()


    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )


    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password)
    )


    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    return {
        "message":"User registered",
        "id":new_user.id
    }




# ---------------- LOGIN ----------------


@app.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    db_user = db.query(User).filter(
        User.email == user.email
    ).first()


    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    if not verify_password(
        user.password,
        db_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Wrong password"
        )


    token = create_access_token(
        {
            "sub":db_user.email
        }
    )


    return {
        "access_token":token,
        "token_type":"bearer"
    }




# ---------------- PROFILE ----------------


@app.get("/profile")
def profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    email = get_current_user_email(
        credentials.credentials
    )


    return {
        "email":email
    }





# ---------------- EXPENSE CREATE ----------------


@app.post("/expenses")
def create_expense(
    expense: ExpenseCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    email = get_current_user_email(
        credentials.credentials
    )


    user = db.query(User).filter(
        User.email == email
    ).first()


    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        user_id=user.id
    )


    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)


    return new_expense




# ---------------- GET EXPENSES ----------------


@app.get("/expenses")
def get_expenses(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    email = get_current_user_email(token)

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user = db.query(User).filter(
        User.email == email
    ).first()


    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    expenses = db.query(Expense).filter(
        Expense.user_id == user.id
    ).all()


    return {
        "user": user.email,
        "count": len(expenses),
        "expenses": expenses
    }



# ---------------- UPDATE EXPENSE ----------------


@app.put("/expenses/{expense_id}")
def update_expense(
    expense_id:int,
    data:ExpenseUpdate,
    db:Session=Depends(get_db)
):

    expense=db.query(Expense).filter(
        Expense.id==expense_id
    ).first()


    if not expense:
        raise HTTPException(404,"Expense not found")


    if data.title:
        expense.title=data.title

    if data.amount:
        expense.amount=data.amount

    if data.category:
        expense.category=data.category


    db.commit()

    return {
        "message":"Expense updated"
    }




# ---------------- DELETE EXPENSE ----------------


@app.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id:int,
    db:Session=Depends(get_db)
):

    expense=db.query(Expense).filter(
        Expense.id==expense_id
    ).first()


    if not expense:
        raise HTTPException(404,"Not found")


    db.delete(expense)
    db.commit()


    return {
        "message":"Deleted"
    }





# ---------------- CREATE BUDGET ----------------


@app.post("/budget")
def create_budget(
    budget:BudgetCreate,
    credentials:HTTPAuthorizationCredentials=Depends(security),
    db:Session=Depends(get_db)
):

    email=get_current_user_email(
        credentials.credentials
    )


    user=db.query(User).filter(
        User.email==email
    ).first()


    new_budget=Budget(
        month=budget.month,
        budget_amount=budget.budget_amount,
        user_id=user.id
    )


    db.add(new_budget)
    db.commit()


    return {
        "message":"Budget created"
    }




# ---------------- GET BUDGET ----------------


@app.get("/budget")
def get_budget(
    credentials:HTTPAuthorizationCredentials=Depends(security),
    db:Session=Depends(get_db)
):

    email=get_current_user_email(
        credentials.credentials
    )


    user=db.query(User).filter(
        User.email==email
    ).first()


    return db.query(Budget).filter(
        Budget.user_id==user.id
    ).all()

#--update_budget --

@app.put("/budget/{id}")
def update_budget(
    id:int,
    data:BudgetUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db:Session = Depends(get_db)
):

    email = get_current_user_email(
        credentials.credentials
    )

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user = db.query(User).filter(
        User.email == email
    ).first()


    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    budget = db.query(Budget).filter(
        Budget.id == id,
        Budget.user_id == user.id
    ).first()


    if budget is None:
        raise HTTPException(
            status_code=404,
            detail="Budget not found for this user"
        )


    if data.month is not None:
        budget.month = data.month


    if data.budget_amount is not None:
        budget.budget_amount = data.budget_amount


    db.commit()
    db.refresh(budget)


    return {
        "message":"Budget updated successfully",
        "budget":budget
    }

#  --delete_budget --
@app.delete("/budget/{id}")
def delete_budget(
    id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    # get token
    token = credentials.credentials

    # get email from token
    email = get_current_user_email(token)

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    # find user
    user = db.query(User).filter(
        User.email == email
    ).first()


    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    # find budget of logged-in user
    budget = db.query(Budget).filter(
        Budget.id == id,
        Budget.user_id == user.id
    ).first()


    if budget is None:
        raise HTTPException(
            status_code=404,
            detail="Budget not found"
        )


    db.delete(budget)
    db.commit()


    return {
        "message": "Budget deleted successfully",
        "deleted_budget_id": id
    }



# ==========================
# DASHBOARD
# ==========================

@app.get("/dashboard")
def dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    email = get_current_user_email(
        credentials.credentials
    )

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user = db.query(User).filter(
        User.email == email
    ).first()


    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    expenses = db.query(Expense).filter(
        Expense.user_id == user.id
    ).all()


    budgets = db.query(Budget).filter(
        Budget.user_id == user.id
    ).all()



    total_expense = sum(
        e.amount for e in expenses
    )


    total_budget = sum(
        b.budget_amount for b in budgets
    )


    remaining = total_budget - total_expense



    return {

        "username": user.username,

        "total_budget": total_budget,

        "total_expense": total_expense,

        "remaining": remaining,


        "expenses": expenses,

        "budgets": budgets
    }




# ==========================
# EXPENSE LIST
# ==========================

@app.get("/expenses-list")
def expenses_list(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    email = get_current_user_email(
        credentials.credentials
    )


    user = db.query(User).filter(
        User.email == email
    ).first()


    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    return db.query(Expense).filter(
        Expense.user_id == user.id
    ).all()





# ==========================
# BUDGET LIST
# ==========================

@app.get("/budgets-list")
def budgets_list(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    email = get_current_user_email(
        credentials.credentials
    )


    user = db.query(User).filter(
        User.email == email
    ).first()


    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    return db.query(Budget).filter(
        Budget.user_id == user.id
    ).all()