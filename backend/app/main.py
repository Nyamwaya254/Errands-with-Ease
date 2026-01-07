from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def router():
    return {"message": "Hello World"}
