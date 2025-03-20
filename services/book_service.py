#book_service.py

import requests

# Replace with your actual Google Books API Key
API_KEY = "AIzaSyA_fuGdiC7fhkjXmg5ltdHf0YAzWIy7xw4"
BASE_URL = "https://www.googleapis.com/books/v1/volumes"

def get_books(query="fiction", max_results=10):
    """Fetch books from Google Books API based on a query."""
    params = {
        "q": query,
        "maxResults": max_results,
        "key": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        books = []
        
        for item in data.get("items", []):
            volume_info = item.get("volumeInfo", {})
            books.append({
                "title": volume_info.get("title", "Unknown Title"),
                "author": ", ".join(volume_info.get("authors", ["Unknown Author"])),
                "rating": volume_info.get("averageRating", "N/A"),
                "genres": volume_info.get("categories", ["N/A"]),
                "summary": volume_info.get("description", "No description available."),
                "image": volume_info.get("imageLinks", {}).get("thumbnail", "https://via.placeholder.com/150"),
                "preview_link": volume_info.get("previewLink", "#")
            })
        return books
    return []

def get_book_details(title):
    """Fetch detailed book info from Google Books API."""
    books = get_books(query=title, max_results=1)
    return books[0] if books else None

def get_recommendations(book_title):
    """Fetch recommended books based on the selected book title."""
    books = get_books()  # Ensure this function fetches book data properly
    recommended = [book for book in books if book["title"] != book_title][:5]  # Simple recommendation logic
    return recommended

