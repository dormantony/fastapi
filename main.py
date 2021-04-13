from fastapi import FastAPI


app=FastAPI()

@app.get('/testo')
def index():
    return {'data': {'name':'Dormant'}}



#uvicorn main:app --reload
