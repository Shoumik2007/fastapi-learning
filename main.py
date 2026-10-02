from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String
from database import Base, engine, SessionLocal

app = FastAPI()

students = []
## pydantic model
class Student(BaseModel):
    name: str
    branch: str
    age: int

class StudentResponse(BaseModel):
    id: int
    name: str
    branch: str
    age: int

    model_config = ConfigDict(from_attributes=True)

##SQAlchemy model

class StudentDB(Base):
    __tablename__ = "students"
    
    id= Column(Integer, primary_key=True, index=True) ## gives unique database ID automatically
    name= Column(String)
    branch= Column(String)
    age= Column(Integer)
    
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/students",response_model=StudentResponse)
def create_student(student: Student, db = Depends(get_db)):
    db_student = StudentDB(
        name= student.name,
        branch= student.branch,
        age= student.age
    )
    
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    return db_student


@app.get("/students", response_model=list[StudentResponse])
def get_students(db= Depends(get_db)):
    return db.query(StudentDB).all()   

@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db=Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()  ## student = incoming data

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return student

@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student: Student, db=Depends(get_db)):
    db_student = db.query(StudentDB).filter(StudentDB.id == student_id).first()     ## db_student = existing data

    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    db_student.name = student.name
    db_student.branch = student.branch
    db_student.age = student.age

    db.commit()
    db.refresh(db_student)

    return db_student

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db=Depends(get_db)):
    db_student = db.query(StudentDB).filter(StudentDB.id == student_id).first()

    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(db_student)
    db.commit()

    return {"message": "Student deleted successfully"}