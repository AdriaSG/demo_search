import os
import pickle
import string
import zipfile

import pandas as pd
import streamlit as st
from sentence_transformers import CrossEncoder, SentenceTransformer
from sklearn.feature_extraction import _stop_words

dir_path = "/usr/src/app/models/data"

# Tokenizer helper for BM25
def bm25_tokenizer(text):
    tokenized_doc = []
    for token in text.lower().split():
        token = token.strip(string.punctuation)
        if len(token) > 0 and token not in _stop_words.ENGLISH_STOP_WORDS:
            tokenized_doc.append(token)
    return tokenized_doc


# Load the pickled data
@st.cache_resource(show_spinner="Fetching GreenDB...")
def get_data():
    with zipfile.ZipFile(os.path.join(dir_path, "greedb_short.p.zip"), "r") as myzip:
        with myzip.open("greedb_short.p", "r") as f:
            products = pickle.load(f)
    products_short = products[
        ["name", "categories", "brand", "sustainability_labels", "colors", "url"]
    ]
    mask = ~products["sustainability_labels"].apply(
        lambda x: "certificate:OTHER" not in x and "certificate:UNKNOWN" not in x
    )
    filter_credible_products = products.index[mask]
    return (products, products_short, filter_credible_products)


# Load the pickled bm25 index
@st.cache_resource(show_spinner="Fetching BM25 corpus...")
def get_bm25():
    with zipfile.ZipFile(
        os.path.join(dir_path, "bm25_corpus_embeddings.p.zip"), "r"
    ) as myzip:
        with myzip.open("bm25_corpus_embeddings.p", "r") as f:
            return pickle.load(f)


# Load the pickled bi-encoder sbert embeddings
@st.cache_resource(show_spinner="Fetching SBERT embeddings...")
def get_sbert_embeddings():
    with zipfile.ZipFile(
        os.path.join(
            dir_path, "multi-qa-mpnet-base-dot-v1_greendb_corpus_embeddings.p.zip"
        ),
        "r",
    ) as myzip:
        with myzip.open(
            "multi-qa-mpnet-base-dot-v1_greendb_corpus_embeddings.p", "r"
        ) as f:
            return pickle.load(f)


# Set up the models
@st.cache_resource(show_spinner="Load bi-encoder model...")
def load_biencoder():
    return SentenceTransformer("/usr/src/app/models/multi-qa-mpnet-base-dot-v1")


@st.cache_resource(show_spinner="Load cross-encoder model...")
def load_crossencoder():
    return CrossEncoder("/usr/src/app/models/stsb-distilroberta-base_plus_easy")


# Not in use !!!
def read_greendb(path):
    products = pd.read_parquet(path)
    print(len(products), "products loaded")
    # Further deduplication, drop deuplicated gtins and asins
    products_null_id = products[(products.gtin.isna()) & (products.asin.isna())]
    depuplicated_ids = products.drop_duplicates(subset=["gtin", "asin"], keep="first")
    products = pd.concat([products_null_id, depuplicated_ids])
    print(len(products), "products after deduplication")
    products["categories_str"] = array_to_str(products["categories"])
    products["color_str"] = array_to_str(products["colors"])
    products["color_str"] = products["color_str"].fillna("")
    products["description"] = products["description"].fillna("")
    products["brand"] = products["brand"].fillna("")
    products["attributes_concat"] = (
        products["name"]
        + products["description"]
        + products["brand"]
        + products["color_str"]
    )
    return products


def array_to_str(column):
    list_str = []
    for element in column:
        if element is not None:
            for e in element:
                e_str = str("".join(e))
        else:
            e_str = str("")
        list_str.append(e_str)
    return list_str


def make_clickable(val):
    return '<a href="{}" target="_blank">{}</a>'.format(val, val)
