'''from swiggydataretriver import SwiggyDataRetriever  # Import the class

# Define API Key and JSON file path
google_api_key = "AIzaSyA75km2BQruVC49MdyXCsx4lMshFoginNo"  # Replace with your actual API key
json_file = "swiggy_results.json"

# Create an instance of SwiggyDataRetriever
retriever = SwiggyDataRetriever(json_file, google_api_key)

# Setup the retriever (loads data, processes it, and initializes the QA chain)
retriever.setup()

# Run a query
#user_query = "Sri Manikanta Restaurant"
user_query="What is the rating of Barbeque Nation?"
result = retriever.run_query(user_query)

# Print the result
print(result)'''


from swiggydataretriver import SwiggyDataRetriever  

def main():
    """Main function to fetch restaurant recommendations."""
    google_api_key = "AIzaSyA75km2BQruVC49MdyXCsx4lMshFoginNo"
    json_file = "swiggy_results.json"

    retriever = SwiggyDataRetriever(json_file, google_api_key)
    retriever.setup()

    user_query = "What is the rating of Barbeque Nation?"
    result = retriever.run_query(user_query)

    # ✅ Save output to a file for debugging
    with open("query_output.txt", "w") as f:
        f.write(result)

    print(result)  # ✅ Ensure subprocess captures this output

# ✅ Ensures the script runs only when executed directly
if __name__ == "__main__":
    main()

