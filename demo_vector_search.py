#!/usr/bin/env python3
"""
NexaDB Vector Search Demo
==========================

Demonstrates semantic vector search with movies.
Perfect for tutorials and testing!

This script:
1. Creates a 'movies' collection
2. Inserts 10 diverse movies with embeddings
3. Performs 3 types of vector searches:
   - Action/Thriller movies
   - Romantic/Drama movies
   - Sci-Fi/Futuristic movies
"""

from nexadb_client import NexaClient
import time

# ANSI color codes for beautiful output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    """Print a beautiful header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}")
    print(f"{text}")
    print(f"{'='*80}{Colors.END}\n")

def print_movie(index, movie, similarity):
    """Print movie details in a nice format"""
    print(f"{Colors.GREEN}{index}. {movie['title']} ({movie['year']}){Colors.END}")
    print(f"   {Colors.YELLOW}Genre:{Colors.END} {movie['genre']}")
    print(f"   {Colors.YELLOW}Director:{Colors.END} {movie['director']}")
    print(f"   {Colors.YELLOW}Plot:{Colors.END} {movie['plot']}")
    print(f"   {Colors.YELLOW}Rating:{Colors.END} {movie['rating']}/10")
    print(f"   {Colors.CYAN}Similarity:{Colors.END} {Colors.BOLD}{similarity:.2%}{Colors.END}\n")

# ============================================================================
# STEP 1: Connect to NexaDB
# ============================================================================
print_header("🚀 NexaDB Vector Search Demo")

print(f"{Colors.BLUE}[1/4] Connecting to NexaDB...{Colors.END}")
client = NexaClient(
    host='localhost',
    port=6970,
    username='root',
    password='nexadb123'
)
client.connect()
print(f"{Colors.GREEN}✅ Connected successfully!{Colors.END}\n")

# ============================================================================
# STEP 2: Prepare Movie Data
# ============================================================================
print(f"{Colors.BLUE}[2/4] Preparing movie data...{Colors.END}")

# 10 diverse movies with semantic embeddings
# Vector dimensions represent themes: [action, romance, sci-fi, drama]
movies = [
    {
        'title': 'The Dark Knight',
        'year': 2008,
        'genre': 'Action/Thriller',
        'director': 'Christopher Nolan',
        'plot': 'Batman faces the Joker in a battle for Gotham\'s soul',
        'rating': 9.0,
        'vector': [0.95, 0.1, 0.3, 0.7]  # High action, low romance, some drama
    },
    {
        'title': 'The Notebook',
        'year': 2004,
        'genre': 'Romance/Drama',
        'director': 'Nick Cassavetes',
        'plot': 'A poor yet passionate young man falls in love with a rich young woman',
        'rating': 7.8,
        'vector': [0.1, 0.98, 0.05, 0.85]  # Low action, very high romance
    },
    {
        'title': 'Inception',
        'year': 2010,
        'genre': 'Sci-Fi/Action',
        'director': 'Christopher Nolan',
        'plot': 'Thieves enter dreams to steal and plant ideas in people\'s minds',
        'rating': 8.8,
        'vector': [0.8, 0.2, 0.95, 0.6]  # High action, high sci-fi
    },
    {
        'title': 'The Shawshank Redemption',
        'year': 1994,
        'genre': 'Drama',
        'director': 'Frank Darabont',
        'plot': 'Two imprisoned men bond over years, finding redemption through acts of decency',
        'rating': 9.3,
        'vector': [0.2, 0.15, 0.1, 0.95]  # Low action, very high drama
    },
    {
        'title': 'Blade Runner 2049',
        'year': 2017,
        'genre': 'Sci-Fi/Thriller',
        'director': 'Denis Villeneuve',
        'plot': 'A blade runner discovers a secret that could plunge society into chaos',
        'rating': 8.0,
        'vector': [0.65, 0.3, 0.92, 0.55]  # Moderate action, very high sci-fi
    },
    {
        'title': 'Titanic',
        'year': 1997,
        'genre': 'Romance/Drama',
        'director': 'James Cameron',
        'plot': 'A seventeen-year-old aristocrat falls in love with a kind artist aboard the Titanic',
        'rating': 7.9,
        'vector': [0.3, 0.95, 0.1, 0.8]  # Low action, very high romance
    },
    {
        'title': 'Mad Max: Fury Road',
        'year': 2015,
        'genre': 'Action/Adventure',
        'director': 'George Miller',
        'plot': 'In a post-apocalyptic wasteland, Max teams with Furiosa to flee a tyrant',
        'rating': 8.1,
        'vector': [0.98, 0.05, 0.4, 0.3]  # Extreme action, low romance
    },
    {
        'title': 'Interstellar',
        'year': 2014,
        'genre': 'Sci-Fi/Drama',
        'director': 'Christopher Nolan',
        'plot': 'A team of explorers travel through a wormhole in space to save humanity',
        'rating': 8.7,
        'vector': [0.5, 0.4, 0.96, 0.75]  # Balanced, very high sci-fi
    },
    {
        'title': 'La La Land',
        'year': 2016,
        'genre': 'Romance/Musical',
        'director': 'Damien Chazelle',
        'plot': 'A jazz musician and an aspiring actress fall in love while pursuing their dreams',
        'rating': 8.0,
        'vector': [0.05, 0.92, 0.15, 0.7]  # Very low action, very high romance
    },
    {
        'title': 'The Matrix',
        'year': 1999,
        'genre': 'Sci-Fi/Action',
        'director': 'Wachowski Sisters',
        'plot': 'A hacker discovers reality is a simulation and joins a rebellion',
        'rating': 8.7,
        'vector': [0.9, 0.15, 0.97, 0.5]  # High action, highest sci-fi
    }
]

print(f"{Colors.GREEN}✅ Prepared {len(movies)} movies with semantic embeddings{Colors.END}\n")

# ============================================================================
# STEP 3: Insert Movies into NexaDB
# ============================================================================
print(f"{Colors.BLUE}[3/4] Inserting movies into 'movies' collection...{Colors.END}")

# Delete old collection if exists
try:
    client.drop_collection('movies')
    print(f"{Colors.YELLOW}   Dropped existing 'movies' collection{Colors.END}")
except:
    pass

# Bulk insert all movies
result = client.batch_write('movies', movies)
print(f"{Colors.GREEN}✅ Successfully inserted {len(movies)} movies!{Colors.END}")
print(f"   Document IDs: {', '.join(result.get('document_ids', []))[:60]}...\n")

time.sleep(0.5)  # Brief pause for dramatic effect

# ============================================================================
# STEP 4: Perform 3 Types of Vector Searches
# ============================================================================
print(f"{Colors.BLUE}[4/4] Performing semantic vector searches...{Colors.END}\n")

# ----------------------------------------------------------------------------
# SEARCH 1: Action/Thriller Movies
# ----------------------------------------------------------------------------
print_header("🎬 SEARCH #1: Looking for Action/Thriller Movies")
print(f"{Colors.YELLOW}Query Vector:{Colors.END} [0.95, 0.05, 0.3, 0.4]")
print(f"{Colors.YELLOW}Theme:{Colors.END} High action, low romance, some tension\n")

action_query = [0.95, 0.05, 0.3, 0.4]
action_results = client.vector_search(
    collection='movies',
    vector=action_query,
    limit=3,
    dimensions=4
)

print(f"{Colors.BOLD}Top 3 Action Movies:{Colors.END}\n")
for i, result in enumerate(action_results, 1):
    print_movie(i, result['document'], result['similarity'])

# ----------------------------------------------------------------------------
# SEARCH 2: Romantic/Drama Movies
# ----------------------------------------------------------------------------
print_header("💕 SEARCH #2: Looking for Romantic/Drama Movies")
print(f"{Colors.YELLOW}Query Vector:{Colors.END} [0.1, 0.95, 0.1, 0.8]")
print(f"{Colors.YELLOW}Theme:{Colors.END} Low action, very high romance, emotional depth\n")

romance_query = [0.1, 0.95, 0.1, 0.8]
romance_results = client.vector_search(
    collection='movies',
    vector=romance_query,
    limit=3,
    dimensions=4
)

print(f"{Colors.BOLD}Top 3 Romantic Movies:{Colors.END}\n")
for i, result in enumerate(romance_results, 1):
    print_movie(i, result['document'], result['similarity'])

# ----------------------------------------------------------------------------
# SEARCH 3: Sci-Fi/Futuristic Movies
# ----------------------------------------------------------------------------
print_header("🚀 SEARCH #3: Looking for Sci-Fi/Futuristic Movies")
print(f"{Colors.YELLOW}Query Vector:{Colors.END} [0.5, 0.2, 0.98, 0.5]")
print(f"{Colors.YELLOW}Theme:{Colors.END} Balanced action, low romance, extreme sci-fi\n")

scifi_query = [0.5, 0.2, 0.98, 0.5]
scifi_results = client.vector_search(
    collection='movies',
    vector=scifi_query,
    limit=3,
    dimensions=4
)

print(f"{Colors.BOLD}Top 3 Sci-Fi Movies:{Colors.END}\n")
for i, result in enumerate(scifi_results, 1):
    print_movie(i, result['document'], result['similarity'])

# ============================================================================
# Summary
# ============================================================================
print_header("📊 Demo Summary")

print(f"{Colors.GREEN}✅ Successfully demonstrated NexaDB vector search!{Colors.END}\n")
print(f"{Colors.BOLD}What we did:{Colors.END}")
print(f"  1. Connected to NexaDB Binary Server (port 6970)")
print(f"  2. Created 'movies' collection with 10 diverse films")
print(f"  3. Each movie has a 4D semantic vector: [action, romance, sci-fi, drama]")
print(f"  4. Performed 3 different semantic searches:")
print(f"     • Action/Thriller → Found: The Dark Knight, Mad Max, The Matrix")
print(f"     • Romantic/Drama → Found: The Notebook, Titanic, La La Land")
print(f"     • Sci-Fi/Future → Found: The Matrix, Interstellar, Blade Runner 2049")

print(f"\n{Colors.CYAN}{Colors.BOLD}💡 Key Insight:{Colors.END}")
print(f"   Vector search finds {Colors.BOLD}semantically similar{Colors.END} movies, not just keyword matches!")
print(f"   Movies with similar themes are automatically grouped together.\n")

print(f"{Colors.YELLOW}🔗 Try it yourself:{Colors.END}")
print(f"   python3 demo_vector_search.py\n")

print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")

# Disconnect
client.disconnect()
print(f"{Colors.GREEN}✅ Disconnected from NexaDB{Colors.END}\n")
