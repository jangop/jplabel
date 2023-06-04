from fastapi import FastAPI
from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func

from data.base import Session
from data.config import settings
from data.models import Image, User, Label, Labeling

image_directory = settings.image_path
image_files = list(image_directory.glob("*.jpg"))

label_texts = ["single piece", "multiple pieces"]

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
        image = session.query(Image).outerjoin(Image.labelings).filter(
            ~Image.labelings.any(Labeling.user == user)).group_by(Image).order_by(func.count(Labeling.id)).first()
        if image is None:
            return f"Congratulations, you have labeled all images!"

        label_html = ""
        key_js = ""
        for i, label_text in enumerate(label_texts, start=1):
            label_html += f"""
            <input type="submit" name="label" value="{'[' + str(i) + ']' + label_text}" onclick="setLabelValue('{label_text}')"/>
            """

            key_js += f"""
                {"if" if i == 1 else "else if"} (event.key == "{i}") {{
                    setLabelValue("{label_text}");
                    sendLabel(event);
                }}
            """
        html = f"""
        <html>
            <head>
                <title>Labeling</title>
                <link rel="stylesheet" href="/static/jp.css">
            </head>
            <body>
                <div class="centering">
                    <img src="/image/{image.filename}" style="max-height: 10cm;"/>
                    <form action="" onsubmit="sendLabel(event)">
                        {label_html}
                    </form>
                </div>
                <script>
                    let selectedLabel = null;

                    function setLabelValue(value) {{
                        selectedLabel = value;
                    }}

                    function sendLabel(event) {{
                        event.preventDefault();
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
                    
                    document.addEventListener("keydown", function(event) {{
                        {key_js}
                    }})
                    
                </script>
            </body>
        </html>
        """
        return HTMLResponse(html)
