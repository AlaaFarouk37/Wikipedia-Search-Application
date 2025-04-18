import wikipedia
import tkinter as tk
from tkinter import messagebox, scrolledtext
import pprint
import sys
import io

user_input = ''
max_articles= 5
positional_index = {}

#text processing
def preprocess_text(text):
    text = text.lower()
    punctuation = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    stop_words = [ 'a', 'an','am', 'the', 'and', 'or', 'but', 'if', 'while', 'with', 'about',
        'against', 'between', 'into', 'through', 'during', 'before', 'after',
        'to', 'from', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
        'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'can', 'will', 'just', 'don', 'should', 'now']

    # Replace punctuation with space
    for p in punctuation:
        text = text.replace(p, ' ')
    
    words = text.split()

    result = []
    for word in words:
        if word not in stop_words:
            stemmed = custom_stemmer(word)
            result.append(stemmed)

    # Join and re-split to remove empty tokens and get final clean list
    return ' '.join(result).split()

#tokenization
def tokenize(text, doc_id):
    words = preprocess_text(text)
    pos = 0
    for word in words:
        update_positional_index(word, doc_id, pos)
        pos += 1

# Stemming function
def custom_stemmer(word):
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("ies") or word.endswith("ied"):
        return word[:-3] + "i"
    if word.endswith("ing") and len(word) > 4:
        return word[:-3]
    if word.endswith("ment"):
        return word[:-4]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def update_positional_index(word,doc_id,pos):
    #to skip invalid characters
    try:
        word = word.encode('ascii', 'ignore').decode()
    except:
        return
    
    # Check if the word exists in the positional index
    if word not in positional_index:
        positional_index[word] = {'doc_freq': 0}

    # Check if the document ID exists for that word
    if doc_id not in positional_index[word]:
        positional_index[word][doc_id] = []
        positional_index[word]['doc_freq']  += 1; 


    positional_index[word][doc_id].append(pos)


#start of merging fucntion
def merge_postings_list():
    tokens = preprocess_text(user_input)
    postings = []

    for token in tokens:
        if token in positional_index:
            #change the postings values inside the dictionary to a list
             postings.append([doc_id for doc_id in positional_index[token] if doc_id != 'doc_freq'])
        else:
            print(f"term '{token}' is not found in index")
    if not postings:
        print('no documents found.')
    else:
        get_intersected_documents(postings)

#helper fucntion for merging
def get_intersected_documents(postings):
    if len(postings)== 1:
        interesected_docs = postings[0]
        get_word_postions(interesected_docs)
        return
        
    list_1 = postings[0]
    interesected_docs = []
    for i in range(1,len(postings)):
        list_2 = postings[i]
        #for query optimization, list_1 must carry the shortest list in length, so we swap if list_2 is shorter
        if len(list_1) > len(list_2 ):
            temp = list_2     
            list_2  = list_1
            list_1 = temp
        #merging process  
        p2 = 0 
        temp_intersection = []
        for p1 in range(0,len(list_1)): #iterates over list_1 and list_2 and stores intersection between them in 'temp_intersection'
            #if p2 is in a valid range and the doc_id is less than doc_id in l1, we increment p2
            while p2 < len(list_2) and list_2[p2] < list_1[p1]:
                p2 +=1

            #if  p2 is in a valid range and the doc_id are equal, we increment p2 while p1 is incremented through the for loop    
            if list_1[p1] == list_2[p2]and p2 < len(list_2):
                temp_intersection.append(list_1[p1])
                p2 +=1
        if not temp_intersection:
            interesected_docs = []
            break
        else:
            if i == 1:
                interesected_docs = temp_intersection
            else:
                interesected_docs = [doc_id for doc_id in interesected_docs if doc_id in temp_intersection] #reduce intersected_docs
        list_1 = interesected_docs
    if not interesected_docs:
        print('no intersection between documents found.')
    else:
        print(f"documents where all words appear (not in order): {interesected_docs}")
        get_word_postions(interesected_docs)

def get_word_postions(intersected_docs):

    tokens = preprocess_text(user_input)
    all_positions = []

    for token in tokens:
        print(f"Token {token}:")
        token_position_in_docs = []
        
        for doc_id in intersected_docs:
            print(f"Document_id: {doc_id}")
            token_position_in_docs.append(positional_index[token][doc_id])
            print(f" in Positions: {positional_index[token][doc_id]}")

        if token_position_in_docs:    
            all_positions.append(token_position_in_docs)

    merge_word_positions(all_positions,tokens,intersected_docs)

def merge_word_positions(all_positions,tokens,intersected_docs):
    phrase_query_match_documents = []
    if len(tokens) == 1:
        phrase_query_match_documents.append(positional_index[tokens[0]])
        print(f"documents where words appear in exact order:  {phrase_query_match_documents}")
        return

    for doc_idx in range(len(intersected_docs)):
        first_token_positions = all_positions[0][doc_idx]

        for start_pos in first_token_positions:
            found_match = True

            for token_offset in range(1, len(tokens)):
                expected_pos = start_pos + token_offset
                current_token_positions = all_positions[token_offset][doc_idx]

                if expected_pos not in current_token_positions:
                    found_match = False
                    break  

            if found_match:
                phrase_query_match_documents.append(intersected_docs[doc_idx])
                break 

    print(f"documents where words appear in exact order{phrase_query_match_documents}")

# Wikipedia Fetch Function with Tokenization and Stopword Removal
def fetch_documents_for_topic():
    print(f"Searching Wikipedia for topic: '{user_input}'...")
    results = wikipedia.search(user_input)

    documents = {}

    for doc_id in range(0,max_articles):
        try:
            page_title = results[doc_id]
            content = wikipedia.page(page_title).content

            # Tokenize and remove stop words
            preprocess_text(content)
            tokenize(content,doc_id)

        except wikipedia.exceptions.DisambiguationError:
            print(f"Skipping disambiguation page: {page_title}")
            continue
        except wikipedia.exceptions.PageError:
            print(f"Page not found: {page_title}")
            continue

def sort_positional_index():
    global positional_index
    sorted_positional_index = {}
    for token in sorted(positional_index.keys()):
        # Sort the posting lists for each token by doc_id 
        sorted_postings = {doc_id: sorted(positions) for doc_id, positions in positional_index[token].items() if doc_id != 'doc_freq'}
        sorted_postings['doc_freq'] = positional_index[token]['doc_freq']

        # Add the sorted token and its postings to the new stored dictionary
        sorted_positional_index[token] = sorted_postings
    positional_index = sorted_positional_index

#display output in the window, not the terminal
class TextRedirector(io.StringIO):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
    def write(self, text):
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)
    def flush(self):
        pass

# Run the search and display results, the command that search button will trigger
def run_search():
    global user_input
    user_input = entry.get().strip()
    output_box.delete(1.0, tk.END)
    if not user_input:
        messagebox.showwarning("Empty Input", "Please enter a phrase to search.")
        return
    
    output_box.insert(tk.END, "Loading...\n")  
    root.update()  

    positional_index.clear()
    try:
        fetch_documents_for_topic()
        sort_positional_index()
        merge_postings_list()
    except Exception as e:
        messagebox.showerror("Error", str(e))

# TKINTER GUI
root = tk.Tk()
root.title("Wikipedia Phrase Search")
root.geometry("750x550")
root.configure(bg="#f0f4f8")  # Light background

frame = tk.Frame(root, padx=20, pady=20, bg="#f0f4f8")
frame.pack(fill=tk.BOTH, expand=True)

title_label = tk.Label(
    frame, text="Wikipedia Phrase Search Engine",
    font=("Helvetica", 18, "bold"), bg="#f0f4f8", fg="#333"
)
title_label.pack(anchor='center', pady=(0, 20))

label = tk.Label(
    frame, text="Enter your phrase:",
    font=("Helvetica", 12), bg="#f0f4f8", fg="#555"
)
label.pack(anchor='w', pady=(0, 5))

entry = tk.Entry(frame, font=("Helvetica", 12), width=50, relief=tk.GROOVE, bd=2)
entry.pack(pady=(0, 10))

search_btn = tk.Button(
    frame, text="Search", command=run_search,
    font=("Helvetica", 11, "bold"),
    bg="#4CAF50", fg="white", padx=10, pady=5,
    activebackground="#45a049", relief=tk.FLAT
)
search_btn.pack(pady=(0, 15))

output_box = scrolledtext.ScrolledText(
    frame, wrap=tk.WORD, font=("Consolas", 11),
    width=85, height=20, relief=tk.SUNKEN, bd=2
)
output_box.pack(fill=tk.BOTH, expand=True)

sys.stdout = TextRedirector(output_box)
root.mainloop()