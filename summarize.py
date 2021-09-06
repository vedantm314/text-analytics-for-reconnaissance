from gensim.summarization.summarizer import summarize
    
def get_summary(df, section, ratio=0.1):
    df = df[df["label"] == section]
    text = " ".join(df["sentence"].tolist())
    text_clean = set(summarize(text, ratio=ratio).split("\n")) # remove duplicated sentences
    return " ".join(text_clean)
