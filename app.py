
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random
from streamlit import rerun
from services.book_service import get_books, get_book_details, get_recommendations

# Set page configuration
st.set_page_config(page_title="Book Catalog", page_icon="📚", layout="wide", initial_sidebar_state="expanded")

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .book-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        transition: transform 0.3s;
    }
    .book-card:hover {
        transform: translateY(-5px);
    }
    .stButton button {
        width: 100%;
        border-radius: 20px;
        font-weight: bold;
    }
    .category-header {
        border-left: 5px solid #ff4b4b;
        padding-left: 10px;
        margin-bottom: 20px;
    }
    .rating-stars {
        color: #FFD700;
        font-size: 18px;
    }
    .sidebar-content {
        padding: 20px;
    }
    .wishlist-item {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
    .progress-bar {
        height: 10px;
        background-color: #ddd;
        border-radius: 5px;
        margin-top: 5px;
    }
    .progress-fill {
        height: 100%;
        border-radius: 5px;
        background-color: #4CAF50;
    }
    .badge {
        background-color: #ff4b4b;
        color: white;
        padding: 3px 10px;
        border-radius: 10px;
        font-size: 12px;
        margin-right: 5px;
    }
    .reading-stats {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "user" not in st.session_state:
    st.session_state.user = None
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []
if "borrowed" not in st.session_state:
    st.session_state.borrowed = []
if "completed" not in st.session_state:
    st.session_state.completed = []
if "reading_progress" not in st.session_state:
    st.session_state.reading_progress = {}
if "reviews" not in st.session_state:
    st.session_state.reviews = {}
if "reading_goal" not in st.session_state:
    st.session_state.reading_goal = 12
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "currently_reading" not in st.session_state:
    st.session_state.currently_reading = None
if "reading_challenge" not in st.session_state:
    st.session_state.reading_challenge = []
if "last_activity" not in st.session_state:
    st.session_state.last_activity = []

# Sidebar Navigation
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/6/6b/Goodreads_logo.png", width=180)
    st.title("📚 Book Catalog")
    
    # User Authentication
    if st.session_state.user:
        st.success(f"👋 Welcome, {st.session_state.user}!")
        st.markdown(f"📊 **Reading Goal:** {len(st.session_state.completed)}/{st.session_state.reading_goal} books")
        
        # Progress bar for reading goal
        progress = min(len(st.session_state.completed) / max(1, st.session_state.reading_goal), 1.0)
        st.progress(progress)
        
        if st.button("📤 Logout"):
            st.session_state.user = None
            st.rerun()
    else:
        with st.expander("🔑 Login / Signup", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                login_tab = st.radio("", ["Login", "Signup"])
            
            if login_tab == "Login":
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("🔐 Login"):
                    if username and password:
                        st.session_state.user = username
                        st.balloons()
                        st.rerun()
            else:
                username = st.text_input("Create Username")
                email = st.text_input("Email")
                password = st.text_input("Create Password", type="password")
                if st.button("✅ Sign Up"):
                    if username and password and email:
                        st.session_state.user = username
                        st.success("Account created successfully!")
                        st.rerun()
    
    # Navigation Menu
    st.subheader("📍 Navigation")
    page = st.radio("", [
        "📖 Home", 
        "🔍 Search", 
        "🧠 Recommendations", 
        "❤️ Wishlist", 
        "📚 Borrowed Books",
        "✅ Completed Books",
        "📊 Analytics", 
        "⚙️ Settings"
    ])
    
    # Currently Reading Section if logged in
    if st.session_state.user and st.session_state.currently_reading:
        st.markdown("---")
        st.subheader("📖 Currently Reading")
        current_book = st.session_state.currently_reading
        st.image(current_book["image"], width=100)
        st.markdown(f"**{current_book['title']}**")
        
        # Reading progress slider
        progress = st.session_state.reading_progress.get(current_book['title'], 0)
        new_progress = st.slider("Your progress:", 0, 100, progress, 5)
        if new_progress != progress:
            st.session_state.reading_progress[current_book['title']] = new_progress
            
            # Add to activity log
            st.session_state.last_activity.insert(0, {
                "action": "updated_progress",
                "book": current_book['title'],
                "progress": new_progress,
                "time": datetime.now().strftime("%b %d, %Y %H:%M")
            })
    
    # Reading Stats
    if st.session_state.user:
        st.markdown("---")
        st.markdown("### 📈 Your Stats")
        books_read = len(st.session_state.completed)
        wishlist_count = len(st.session_state.wishlist)
        borrowed_count = len(st.session_state.borrowed)
        
        col1, col2 = st.columns(2)
        col1.metric("Read", books_read)
        col2.metric("To Read", wishlist_count)
        
        # Badge system
        if books_read >= 5:
            st.markdown("🏆 **Badges:**")
            badges = []
            if books_read >= 5:
                badges.append("Bookworm")
            if books_read >= 10:
                badges.append("Literature Lover")
            if len(st.session_state.reviews) >= 3:
                badges.append("Critic")
                
            for badge in badges:
                st.markdown(f"<span class='badge'>{badge}</span>", unsafe_allow_html=True)

# Load book data
books = get_books()

# Function to convert rating to stars
def rating_to_stars(rating):
    if rating == "N/A":
        return "☆☆☆☆☆"
    try:
        rating_float = float(rating)
        full_stars = int(rating_float)
        half_star = rating_float - full_stars >= 0.5
        stars = "★" * full_stars
        if half_star:
            stars += "½"
        stars += "☆" * (5 - full_stars - (1 if half_star else 0))
        return stars
    except:
        return "☆☆☆☆☆"

# Function to display books in a modern grid
def display_books(books_list, show_progress=False, show_completion=False):
    if not books_list:
        st.info("No books to display.")
        return
        
    # Display books in responsive grid
    for i in range(0, len(books_list), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(books_list):
                book = books_list[i + j]
                with cols[j]:
                    st.markdown(f"""
                    <div class='book-card'>
                        <img src='{book["image"]}' width='100%' style='border-radius: 5px;'>
                        <h4>{book['title']}</h4>
                        <p>{book['author']}</p>
                        <div class='rating-stars'>{rating_to_stars(book['rating'])}</div>
                    """, unsafe_allow_html=True)
                    
                    # Show reading progress if enabled
                    if show_progress and book['title'] in st.session_state.reading_progress:
                        progress = st.session_state.reading_progress[book['title']]
                        st.markdown(f"""
                        <div class='progress-bar'>
                            <div class='progress-fill' style='width: {progress}%;'></div>
                        </div>
                        <p style='text-align: right; font-size: 12px;'>{progress}% complete</p>
                        """, unsafe_allow_html=True)
                    
                    # Show completion checkbox if enabled
                    if show_completion:
                        is_completed = book['title'] in [b['title'] for b in st.session_state.completed]
                        if st.checkbox("Mark as read", value=is_completed, key=f"complete_{book['title']}"):
                            if not is_completed:
                                st.session_state.completed.append(book)
                                # Add to activity log
                                st.session_state.last_activity.insert(0, {
                                    "action": "completed",
                                    "book": book['title'],
                                    "time": datetime.now().strftime("%b %d, %Y %H:%M")
                                })
                        
                    if st.button(f"View Details", key=f"view_{book['title']}"):
                        st.session_state.selected_book = book["title"]
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

# Pages content
if page == "📖 Home":
    # Hero Section
    st.title("Discover Your Next Favorite Book")
    st.markdown("Explore thousands of books, track your reading progress, and connect with other readers!")
    
    # Featured Books section
    st.markdown("<h2 class='category-header'>📝 Editor's Picks</h2>", unsafe_allow_html=True)
    featured_books = books[:4]  # First 4 books as featured
    display_books(featured_books)
    
    # Recently Added
    st.markdown("<h2 class='category-header'>🆕 Recently Added</h2>", unsafe_allow_html=True)
    recent_books = books[4:8]  # Next 4 books as recent
    display_books(recent_books)
    
    # Reading Activity Feed (if logged in)
    if st.session_state.user and st.session_state.last_activity:
        st.markdown("<h2 class='category-header'>🔄 Recent Activity</h2>", unsafe_allow_html=True)
        activity_container = st.container()
        with activity_container:
            for activity in st.session_state.last_activity[:5]:
                if activity["action"] == "completed":
                    st.markdown(f"📚 You finished reading **{activity['book']}** - {activity['time']}")
                elif activity["action"] == "updated_progress":
                    st.markdown(f"📖 You're {activity['progress']}% through **{activity['book']}** - {activity['time']}")
                elif activity["action"] == "reviewed":
                    st.markdown(f"✍️ You reviewed **{activity['book']}** - {activity['time']}")
                elif activity["action"] == "added_wishlist":
                    st.markdown(f"❤️ You added **{activity['book']}** to your wishlist - {activity['time']}")

# Search Page
if page == "🔍 Search":
    st.title("Find Your Next Great Read")
    
    # Advanced search options
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("🔎 Search by title, author, or keyword", "")
    with col2:
        search_filter = st.selectbox("Filter by:", ["All", "Fiction", "Non-Fiction", "Mystery", "Science Fiction", "Fantasy", "Biography"])
    
    # Search button
    search_pressed = st.button("Search Books")
    
    if search_query or search_pressed:
        search_results = [book for book in books if search_query.lower() in book['title'].lower() 
                          or search_query.lower() in book['author'].lower()]
        
        # Apply filter if not "All"
        if search_filter != "All":
            search_results = [book for book in search_results if search_filter in book.get('genres', [])]
        
        if search_results:
            st.success(f"Found {len(search_results)} books matching your search")
            display_books(search_results)
        else:
            st.warning("No results found. Try different keywords or filters.")
            
        # Suggested searches
        st.markdown("### Suggested searches:")
        suggestions = ["Harry Potter", "Mystery novels", "Stephen King", "Biography", "Classic literature"]
        suggestion_cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            if suggestion_cols[i].button(suggestion):
                # This would ideally update the search field and trigger a search
                pass

# Wishlist Feature
if page == "❤️ Wishlist":
    st.title("My Reading Wishlist")
    
    if not st.session_state.user:
        st.warning("Please log in to manage your wishlist")
    else:
        # Allow sorting of wishlist
        if st.session_state.wishlist:
            sort_option = st.selectbox("Sort by:", ["Recently Added", "Title A-Z", "Author A-Z", "Rating"])
            
            # Sort wishlist based on selection
            sorted_wishlist = st.session_state.wishlist.copy()
            if sort_option == "Title A-Z":
                sorted_wishlist.sort(key=lambda x: x['title'])
            elif sort_option == "Author A-Z":
                sorted_wishlist.sort(key=lambda x: x['author'])
            elif sort_option == "Rating":
                # Sort by rating, handling 'N/A' values
                sorted_wishlist.sort(key=lambda x: float(x['rating']) if x['rating'] != 'N/A' else 0, reverse=True)
            
            # Display wishlist with reading progress tracking
            display_books(sorted_wishlist, show_progress=True, show_completion=True)
            
            # Bulk actions
            st.markdown("### Bulk Actions")
            bulk_action = st.selectbox("With selected items:", ["Select action...", "Mark as reading", "Remove from wishlist"])
            if bulk_action != "Select action..." and st.button("Apply"):
                st.info(f"Bulk action '{bulk_action}' would be applied here")
        else:
            st.info("Your wishlist is empty. Browse books and add them to your wishlist!")
            
            # Suggested books to add
            st.markdown("### Recommended for your wishlist:")
            recommended = books[:3]  # Just showing first 3 books as suggestions
            display_books(recommended)

# Borrowed Books Feature
if page == "📚 Borrowed Books":
    st.title("My Borrowed Books")
    
    if not st.session_state.user:
        st.warning("Please log in to track borrowed books")
    else:
        # Date filters for borrowed books
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by status:", ["All", "Currently Reading", "Not Started", "Returned"])
        with col2:
            # This would normally filter by borrow date
            sort_by = st.selectbox("Sort by:", ["Borrow Date (Newest)", "Borrow Date (Oldest)", "Due Date"])
        
        if not st.session_state.borrowed:
            st.info("You haven't borrowed any books yet.")
        else:
            # In a real app, we'd filter based on the selections above
            display_books(st.session_state.borrowed, show_progress=True)
            
            # Due date tracker (dummy data for demonstration)
            st.markdown("### 📅 Due Dates")
            for i, book in enumerate(st.session_state.borrowed):
                due_date = (datetime.now().day + (i+1)*7) % 28 + 1
                due_month = datetime.now().month
                st.markdown(f"**{book['title']}** - Due: {due_month}/{due_date}/2023")

# Completed Books Feature
if page == "✅ Completed Books":
    st.title("My Completed Books")
    
    if not st.session_state.user:
        st.warning("Please log in to see your completed books")
    else:
        # Stats for completed books
        if st.session_state.completed:
            col1, col2, col3 = st.columns(3)
            col1.metric("Books Read", len(st.session_state.completed))
            col2.metric("This Month", len(st.session_state.completed) // 2)  # Dummy data
            col3.metric("Goal Progress", f"{min(100, int(len(st.session_state.completed) / st.session_state.reading_goal * 100))}%")
            
            # Filter and display completed books
            year_filter = st.selectbox("Filter by year:", ["All Years", "2023", "2022", "2021"])
            
            # Show completed books with option to add reviews
            for i in range(0, len(st.session_state.completed), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(st.session_state.completed):
                        book = st.session_state.completed[i + j]
                        with cols[j]:
                            st.markdown(f"""
                            <div class='book-card'>
                                <img src='{book["image"]}' width='100%' style='border-radius: 5px;'>
                                <h4>{book['title']}</h4>
                                <p>{book['author']}</p>
                                <div class='rating-stars'>{rating_to_stars(book['rating'])}</div>
                            """, unsafe_allow_html=True)
                            
                            # Check if book has been reviewed
                            has_review = book['title'] in st.session_state.reviews
                            
                            if has_review:
                                st.markdown(f"**Your Review:** {st.session_state.reviews[book['title']]['text'][:50]}...")
                                st.markdown(f"**Your Rating:** {rating_to_stars(str(st.session_state.reviews[book['title']]['rating']))}")
                            
                            if st.button(f"{'Edit Review' if has_review else 'Add Review'}", key=f"review_{book['title']}"):
                                st.session_state.review_book = book
                                st.rerun()
                                
                            st.markdown("</div>", unsafe_allow_html=True)
            
            # Review Form
            if "review_book" in st.session_state:
                st.markdown("### Add Your Review")
                book = st.session_state.review_book
                st.markdown(f"**Book:** {book['title']}")
                
                # Get existing review if any
                existing_review = st.session_state.reviews.get(book['title'], {'text': '', 'rating': 5})
                
                user_rating = st.slider("Your Rating:", 1, 5, existing_review['rating'])
                user_review = st.text_area("Your Review:", value=existing_review['text'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Review"):
                        st.session_state.reviews[book['title']] = {
                            'text': user_review,
                            'rating': user_rating,
                            'date': datetime.now().strftime("%b %d, %Y")
                        }
                        # Add to activity log
                        st.session_state.last_activity.insert(0, {
                            "action": "reviewed",
                            "book": book['title'],
                            "rating": user_rating,
                            "time": datetime.now().strftime("%b %d, %Y %H:%M")
                        })
                        del st.session_state.review_book
                        st.rerun()
                with col2:
                    if st.button("Cancel"):
                        del st.session_state.review_book
                        st.rerun()
        else:
            st.info("You haven't completed any books yet. When you finish a book, mark it as read!")
            st.markdown("### Reading Challenge")
            st.markdown("Set a reading goal to keep yourself motivated!")
            new_goal = st.number_input("Books to read this year:", min_value=1, max_value=100, value=st.session_state.reading_goal)
            if new_goal != st.session_state.reading_goal and st.button("Update Goal"):
                st.session_state.reading_goal = new_goal
                st.success(f"Reading goal updated to {new_goal} books!")

# Recommendations Feature
if page == "🧠 Recommendations":
    st.title("Book Recommendations For You")
    
    if not st.session_state.user:
        st.warning("Please log in to get personalized recommendations")
        # Show general recommendations for non-logged users
        st.markdown("### Popular Books")
        display_books(books[:4])
    else:
        # Tabs for different recommendation categories
        tab1, tab2, tab3 = st.tabs(["Based on Your Taste", "Popular Now", "New Releases"])
        
        with tab1:
            if "selected_book" in st.session_state:
                recommended_books = get_recommendations(st.session_state.selected_book)
                display_books([book for book in books if book['title'] in recommended_books])
            elif st.session_state.completed:
                # Get recommendations based on completed books
                st.markdown("### Based on books you've read")
                # In a real app, we'd use a recommendation algorithm
                random.shuffle(books)  # Just for demo to show different books each time
                display_books(books[:4])
            else:
                st.info("Complete some books or click on a book to get recommendations based on your taste!")
        
        with tab2:
            st.markdown("### Trending This Week")
            display_books(books[4:8])
            
        with tab3:
            st.markdown("### Hot Off the Press")
            display_books(books[8:12])
            
        # Reading challenges section
        st.markdown("### 🏆 Reading Challenges")
        challenges = [
            "Read 5 books from different genres",
            "Complete a book series",
            "Read a book published this year",
            "Read a classic novel",
            "Read a book recommended by a friend"
        ]
        
        for i, challenge in enumerate(challenges):
            completed = i in st.session_state.reading_challenge
            if st.checkbox(challenge, value=completed, key=f"challenge_{i}"):
                if not completed:
                    st.session_state.reading_challenge.append(i)
            
        # Challenge progress
        challenge_progress = len(st.session_state.reading_challenge) / len(challenges)
        st.progress(challenge_progress)
        st.markdown(f"**Challenge Progress:** {len(st.session_state.reading_challenge)}/{len(challenges)} completed")

# Analytics Page
if page == "📊 Analytics":
    st.title("Your Reading Insights")
    
    if not st.session_state.user:
        st.warning("Please log in to see your reading analytics")
        
        # Show general statistics for non-logged users
        st.markdown("### Global Reading Trends")
        genre_count = pd.Series([genre for book in books for genre in book.get('genres', [])]).value_counts()
        st.bar_chart(genre_count)
    else:
        # Reading Stats Dashboard
        st.markdown("### 📈 Your Reading Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Books Read", len(st.session_state.completed))
        col2.metric("In Progress", len([b for b in st.session_state.borrowed if b['title'] in st.session_state.reading_progress]))
        col3.metric("To-Read", len(st.session_state.wishlist))
        col4.metric("Reviews Written", len(st.session_state.reviews))
        
        # Reading Pace (dummy data for demonstration)
        st.markdown("### 🏃‍♂️ Reading Pace")
        reading_pace = [
            {"month": "Jan", "books": 1},
            {"month": "Feb", "books": 2},
            {"month": "Mar", "books": 1},
            {"month": "Apr", "books": 3},
            {"month": "May", "books": 2},
            {"month": "Jun", "books": 1},
        ]
        pace_df = pd.DataFrame(reading_pace)
        st.line_chart(pace_df.set_index("month"))
        
        # Genre Distribution
        st.markdown("### 🏷️ Your Genre Preferences")
        if st.session_state.completed:
            genre_count = pd.Series([genre for book in st.session_state.completed for genre in book.get('genres', [])]).value_counts()
            st.bar_chart(genre_count)
            
            # Most read authors
            st.markdown("### 👨‍🎨 Your Favorite Authors")
            author_count = pd.Series([book.get('author') for book in st.session_state.completed]).value_counts().head(5)
            st.bar_chart(author_count)
        else:
            st.info("Complete some books to see your reading statistics!")
            
        # Reading Heatmap
        st.markdown("### 📅 Reading Activity Heatmap")
        st.markdown("A visualization of your reading activity would appear here, showing which days you read the most.")
        
        # Export options
        st.markdown("### 📤 Export Your Data")
        export_format = st.selectbox("Choose format:", ["CSV", "Excel", "PDF"])
        if st.button(f"Export Reading History as {export_format}"):
            st.success(f"Your reading history would be exported as {export_format}")

# Settings Page
if page == "⚙️ Settings":
    st.title("Account Settings")
    
    if not st.session_state.user:
        st.warning("Please log in to access settings")
    else:
        # Profile Settings
        st.markdown("### 👤 Profile Settings")
        col1, col2 = st.columns(2)
        with col1:
            display_name = st.text_input("Display Name", value=st.session_state.user)
            email = st.text_input("Email Address", value="user@example.com")
        with col2:
            bio = st.text_area("Bio", value="Book lover and avid reader")
            privacy = st.selectbox("Profile Privacy", ["Public", "Friends Only", "Private"])
        
        if st.button("Update Profile"):
            st.success("Profile would be updated (simulation)")
        
        # Reading Preferences
        st.markdown("### 📚 Reading Preferences")
        favorite_genres = st.multiselect(
            "Favorite Genres",
            ["Fiction", "Non-Fiction", "Mystery", "Science Fiction", "Fantasy", "Biography", "History", "Romance"],
            ["Fiction", "Mystery"]
        )
        
        reading_goal = st.number_input("Annual Reading Goal (Books)", min_value=1, value=st.session_state.reading_goal)
        
        if st.button("Save Preferences"):
            st.session_state.reading_goal = reading_goal
            st.success("Preferences saved!")
        
        # Notification Settings
        st.markdown("### 🔔 Notification Settings")
        st.checkbox("Email notifications for recommendations", value=True)
        st.checkbox("Reading reminders", value=True)
        st.checkbox("New book alerts for favorite authors", value=True)
        
        # Theme Settings
        st.markdown("### 🎨 Theme Settings")
        dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()  # This would normally apply the theme
            
        # Data Management
        st.markdown("### 🗄️ Data Management")
        if st.button("Export All Data"):
            st.success("Your data export is being prepared (simulation)")
            
        if st.button("Delete Account", type="primary"):
            st.error("This will permanently delete your account and all your data!")
            confirm = st.checkbox("I understand this action cannot be undone")
            if confirm and st.button("Confirm Delete Account"):
                st.warning("Account would be deleted (simulation)")
                st.session_state.user = None
                st.rerun()

# Book Details
if "selected_book" in st.session_state:
    selected_book = st.session_state.selected_book
    details = get_book_details(selected_book)
    
    # Book details header
    st.title(details["title"])
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(details["image"], width=200)
        
        # Action buttons
        button_col1, button_col2 = st.columns(2)
        with button_col1:
            wishlist_status = details in st.session_state.wishlist
            if st.button("❤️ " + ("In Wishlist" if wishlist_status else "Add to Wishlist")):
                if not wishlist_status:
                    st.session_state.wishlist.append(details)
                    # Add to activity log
                    st.session_state.last_activity.insert(0, {
                        "action": "added_wishlist",
                        "book": details['title'],
                        "time": datetime.now().strftime("%b %d, %Y %H:%M")
                    })
                    st.success("Added to Wishlist!")
                else:
                    st.info("Already in your Wishlist!")
                    st.session_state.wishlist = [b for b in st.session_state.wishlist if b['title'] != details['title']]
                    st.success("Removed from Wishlist!")
                st.rerun()
                
        with button_col2:
            if st.button("📖 Start Reading"):
                st.session_state.currently_reading = details
                st.session_state.reading_progress[details['title']] = st.session_state.reading_progress.get(details['title'], 0)
                # Add to activity log
                st.session_state.last_activity.insert(0, {
                    "action": "started_reading",
                    "book": details['title'],
                    "time": datetime.now().strftime("%b %d, %Y %H:%M")
                })
                st.success(f"You're now reading {details['title']}!")
                st.rerun()
    
    with col2:
        st.markdown(f"**Author:** {details['author']}")
        st.markdown(f"**Rating:** {rating_to_stars(details['rating'])}")
        
        if details.get('genres'):
            st.markdown("**Genres:** " + ", ".join(details['genres']))
        
        if details.get('summary'):
            st.markdown("### Summary")
            st.markdown(details['summary'])
            
        # Book Reviews (dummy data for demonstration)
        st.markdown("### 📝 Reviews")
        
        # Check if user has reviewed this book
        if st.session_state.user and details['title'] in st.session_state.reviews:
            user_review = st.session_state.reviews[details['title']]
            st.markdown("### Your Review")
            st.markdown(f"**Rating:** {rating_to_stars(str(user_review['rating']))}")
            st.markdown(f"**Posted on:** {user_review['date']}")
            st.markdown(user_review['text'])
            
            if st.button("Edit Your Review"):
                st.session_state.review_book = details
                st.rerun()
        
        # Other people's reviews (dummy data)
        st.markdown("### Community Reviews")
        dummy_reviews = [
            {"user": "BookLover42", "rating": "4.5", "review": "This book was amazing! The character development was fantastic.", "date": "Feb 15, 2023"},
            {"user": "ReadAllDay", "rating": "3", "review": "Good but not great. The plot was somewhat predictable.", "date": "Jan 22, 2023"}
        ]
        
        for review in dummy_reviews:
            st.markdown(f"**{review['user']}** - {rating_to_stars(review['rating'])}")
            st.markdown(f"*{review['date']}*")
            st.markdown(review['review'])
            st.markdown("---")
            
        # Community Stats
        st.markdown("### 📊 Community Stats")
        col1, col2, col3 = st.columns(3)
        col1.metric("Currently Reading", "127")
        col2.metric("Times Finished", "1,482")
        col3.metric("Avg. Reading Time", "12 days")
            
    # Similar books
    st.subheader("You might also like")
    # Get recommendations based on this book
    similar_books = [book for book in books if book['title'] != details['title']][:4]
    display_books(similar_books)
    
    # Back button
    if st.button("← Back to Browse"):
        del st.session_state.selected_book
        st.rerun()

# Footer
st.markdown("---")
st.markdown("© 2023 Book Catalog App | Powered by Streamlit | Built with ❤️ for book lovers")
                    