from fastapi import FastAPI

from pathlib import Path

from fastapi.responses import FileResponse, HTMLResponse
from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy import func

from data.models import Image, User, Label, Labeling
from data.base import Session
import PIL.Image
from fastapi.staticfiles import StaticFiles

from data.config import settings

image_directory = settings.image_path
image_files = list(image_directory.glob("*.jpg"))

label_texts = ["funny", "dull"]

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

def initial_setup():
    with Session() as session:
        for image_file in image_files:
            image = session.query(Image).filter(Image.filename == image_file.name).one_or_none()
            if image is None:
                image = Image(filename=image_file.name)
                session.add(image)
        for label_text in label_texts:
            label = session.query(Label).filter(Label.text == label_text).one_or_none()
            if label is None:
                label = Label(text=label_text)
                session.add(label)
        session.commit()

initial_setup()

@app.get("/image/{filename}", response_class=FileResponse)
async def serve_image(filename: str):
    path = image_directory / filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Image {filename} not available")
    return FileResponse(path)

from pydantic import BaseModel
class SentLabel(BaseModel):
    username: str
    filename: str
    text: str

@app.post("/label")
async def label_image(sent_label: SentLabel):
    with Session() as session:
        user = session.query(User).filter(User.name == sent_label.username).one_or_none()
        if user is None:
            user = User(name=sent_label.username)
            session.add(user)
        image = session.query(Image).filter(Image.filename == sent_label.filename).one_or_none()
        if image is None:
            image = Image(filename=sent_label.filename)
            session.add(image)
        label = session.query(Label).filter(Label.text == sent_label.text).one_or_none()
        if label is None:
            label = Label(text=sent_label.text)
            session.add(label)
        labeling = Labeling(user=user, image=image, label=label)
        session.add(labeling)
        session.commit()



@app.get("/next-label/{username}", response_class=HTMLResponse)
async def label_next_image(username: str):
    with Session() as session:
        user = session.query(User).filter(User.name == username).one_or_none()
        if user is None:
            user = User(name=username)
            session.add(user)
        image = session.query(Image).outerjoin(Image.labelings).filter(~Image.labelings.any(Labeling.user == user)).group_by(Image).order_by(func.count(Labeling.id)).first()
        if image is None:
            return f"Congratulations, you have labeled all images!"
        html = f"""
        <html>
            <body>
                <img src="/image/{image.filename}" style="max-height: 10cm;"/>
                <form action="" onsubmit="sendLabel(event)">
                    <input type="submit" name="label" value="funny" onclick="setLabelValue('funny')"/>
                    <input type="submit" name="label" value="dull" onclick="setLabelValue('dull')"/>
                </form>
                <script>
                    let selectedLabel = null;

                    function setLabelValue(value) {{
                        selectedLabel = value;
                    }}

                    function sendLabel(event) {{
                        event.preventDefault();
                        const formData = new FormData(event.target);
                        const label = formData.get("label");
                        console.log(label);
                        fetch("/label", {{
                            method: "POST",
                            headers: {{
                                "Content-Type": "application/json"
                            }},
                            body: JSON.stringify({{
                                username: "{username}",
                                filename: "{image.filename}",
                                text: selectedLabel
                            }})
                        }})
                        .then(response => {{
                            if (response.ok) {{
                                window.location.reload();
                            }} else {{
                                alert("Something went wrong!");
                            }}
                        }})
                    }}
                </script>
            </body>
        </html>
        """
        return HTMLResponse(html)
