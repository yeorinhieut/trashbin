import asyncio
import json
import logging
import sqlite3
import os
from typing import List
from urllib.parse import urlparse, urlunparse

import aiohttp
from dc_api import API
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configure logging
logging.basicConfig(filename='error.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
conn = sqlite3.connect('./database.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables if not exist
cursor.execute('''CREATE TABLE IF NOT EXISTS posts
                  (id INTEGER PRIMARY KEY,
                   title TEXT,
                   author TEXT,
                   time TEXT,
                   contents TEXT,
                   images TEXT,
                   isdeleted INTEGER DEFAULT 0,
                   isblinded INTEGER DEFAULT 0)''')
conn.commit()

app = FastAPI()

app.mount("/app", StaticFiles(directory="public", html=True), name="static")

class DeletedPost(BaseModel):
    id: int
    title: str
    author: str
    time: str

class FullPost(BaseModel):
    id: int
    title: str
    author: str
    time: str
    contents: str
    images: List[dict]
    isdeleted: int
    isblinded: int

async def get_user_input():
    if os.path.exists('config.json'):
        print("config.json found. Loading existing configuration.")
        with open('config.json', 'r') as f:
            config = json.load(f)
        gallery_id = config['galleries'][0]['id']
        delay = config['galleries'][0]['delay']
    else:
        print("Welcome to DC Inside Archiver")
        gallery_id = input("Please enter the gallery ID you want to archive: ")
        delay = int(input("Please enter the delay between requests (in seconds): "))
        
        config = {
            "galleries": [
                {
                    "id": gallery_id,
                    "delay": delay
                }
            ]
        }
        
        with open("config.json", "w") as f:
            json.dump(config, f)
        
        print("config.json has been created.")

    print(f"Archiving gallery: {gallery_id} with delay: {delay} seconds")
    return gallery_id, delay

async def get_latest_posts(api, gallery_id, num_latest):
    print(f"Fetching {num_latest} latest posts from gallery {gallery_id}")
    latest_posts = []
    async for index in api.board(board_id=gallery_id, num=num_latest, start_page=1):
        latest_posts.append(index.id)
    print(f"Fetched post numbers: {latest_posts}")
    return sorted(latest_posts)

async def is_post_crawled(id):
    cursor.execute("SELECT COUNT(*) FROM posts WHERE id = ?", (id,))
    count = cursor.fetchone()[0]
    is_crawled = count > 0
    print(f"Checking if post {id} is already crawled: {'Yes' if is_crawled else 'No'} (Count: {count})")
    return is_crawled

async def crawl_post(api, gallery_id, id):
    print(f"Crawling post {id} from gallery {gallery_id}")
    if await is_post_crawled(id):
        print(f"Post {id} already exists in database. Skipping.")
        return
    
    doc = await api.document(board_id=gallery_id, document_id=id)
    if doc:
        await save_post(id, doc)
        print(f"Post saved: {id}")
    else:
        print(f"Post not found: {id}")

async def save_post(id, doc):
    print(f"Saving post {id} to database")
    images = []
    for i, image in enumerate(doc.images, start=1):
        image_url = change_domain(image.src)
        if image_url is not None:
            images.append({"image{}".format(i): image_url})

    time_str = doc.time.isoformat()

    try:
        cursor.execute('''INSERT OR REPLACE INTO posts (id, title, author, time, contents, images)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (id, doc.title, doc.author, time_str, doc.contents, json.dumps(images)))
        conn.commit()
        print(f"Post {id} saved to database successfully")
    except sqlite3.Error as e:
        print(f"An error occurred while saving post {id}: {e}")
    
    # Verify the post was saved
    cursor.execute("SELECT * FROM posts WHERE id = ?", (id,))
    saved_post = cursor.fetchone()
    if saved_post:
        print(f"Post {id} verified in database: {saved_post}")
    else:
        print(f"Post {id} not found in database after save attempt")


def change_domain(url):
    if "dccon.php" in url:
        return None
    parsed = urlparse(url)
    new_netloc = "images.dcinside.com"
    new_url = urlunparse(parsed._replace(netloc=new_netloc))
    print(f"Changed image URL from {url} to {new_url}")
    return new_url

async def check_deleted(gallery_id, id):
    print(f"Checking if post {id} in gallery {gallery_id} is deleted")
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 Mobile Safari/537.36"
    }
    url = f"https://m.dcinside.com/board/{gallery_id}/{id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status in {403, 404}:
                    cursor.execute("UPDATE posts SET isdeleted = 1 WHERE id = ?", (id,))
                    conn.commit()
                    print(f"Post {id} is deleted.")
                else:
                    print(f"Post {id} still exists.")
    except aiohttp.ClientError as e:
        logger.error(f"Error in check_deleted: {e}")
        print(f"Error checking deletion status of post {id}: {e}")

async def crawler_main():
    gallery_id, delay = await get_user_input()
    api = API()
    
    print(f"Starting main crawler loop for gallery {gallery_id}")
    while True:
        try:
            latest_posts = await get_latest_posts(api, gallery_id, 10)
            
            for id in latest_posts:
                if not await is_post_crawled(id):
                    await crawl_post(api, gallery_id, id)
                    asyncio.create_task(delayed_check(gallery_id, id))
            
            print(f"Waiting for {delay} seconds before next batch of requests")
            await asyncio.sleep(delay)  # Wait after processing all 10 posts
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"Error in main crawler loop: {e}")

async def delayed_check(gallery_id, id):
    print(f"Scheduling deletion check for post {id} in 30 minutes")
    await asyncio.sleep(1800)  # Wait for 30 minutes
    await check_deleted(gallery_id, id)

@app.on_event("startup")
async def startup_event():
    print("Starting up the FastAPI application")
    asyncio.create_task(crawler_main())

@app.get("/api/deleted", response_model=List[DeletedPost])
async def get_deleted_posts(page: int = 1):
    print(f"Fetching deleted posts for page {page}")
    offset = (page - 1) * 20
    cursor.execute("""
        SELECT id, title, author, time
        FROM posts
        WHERE isdeleted = 1
        ORDER BY time DESC
        LIMIT 20 OFFSET ?
    """, (offset,))
    deleted_posts = cursor.fetchall()
    print(f"Fetched {len(deleted_posts)} deleted posts")
    return [DeletedPost(id=row[0], title=row[1], author=row[2], time=row[3]) for row in deleted_posts]

@app.get("/api/post", response_model=FullPost)
async def get_post(id: int):
    print(f"Fetching full post details for post id {id}")
    cursor.execute("SELECT * FROM posts WHERE id = ?", (id,))
    post = cursor.fetchone()
    if post is None:
        print(f"Post with id {id} not found in database")
        raise HTTPException(status_code=404, detail="Post not found")
    print(f"Fetched details for post id {id}: {post}")
    return FullPost(
        id=post[0],
        title=post[1],
        author=post[2],
        time=post[3],
        contents=post[4],
        images=json.loads(post[5]),
        isdeleted=post[6],
        isblinded=post[7]
    )

@app.get("/api/database_check")
async def database_check():
    cursor.execute("SELECT COUNT(*) FROM posts")
    total_posts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM posts WHERE isdeleted = 1")
    deleted_posts = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM posts ORDER BY id DESC LIMIT 10")
    latest_posts = [row[0] for row in cursor.fetchall()]
    return {
        "total_posts": total_posts,
        "deleted_posts": deleted_posts,
        "latest_posts": latest_posts
    }

if __name__ == "__main__":
    print("Starting the FastAPI application")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)