from etl import embed, import_weaviate

def main():
    print("Step 1: Embedding text")
    embed.run()

    print("Step 2: Importing into Weaviate")
    import_weaviate.run()

if __name__ == "__main__":
    main()
# embed code here 