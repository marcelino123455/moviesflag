from flask import Flask, render_template, request, jsonify
import requests
import json
import concurrent.futures
from functools import lru_cache

app = Flask(__name__)
apikey = "79076a6d"


def searchfilms(search_text, limit=15): #Cantidad de peliculas q se quiere obtener
    results = []
    page = 1
    while len(results) < limit:
        url = f"https://www.omdbapi.com/?s={search_text}&apikey={apikey}&page={page}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('Response') == 'True':
                results.extend(data['Search'])
                if len(results) >= limit:
                    results = results[:limit]
                    break
                page += 1
            else:
                break
        else:
            break
    
    return {"Search": results, "totalResults": len(results), "Response": "True"}

def getmoviedetails(movie):
    url = "https://www.omdbapi.com/?i=" + movie["imdbID"] + "&apikey=" + apikey
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve search results.")
        return None
    

def getmoviedetails(movie):
    url = "https://www.omdbapi.com/?i=" + movie["imdbID"] + "&apikey=" + apikey
    response = requests.get(url)
    # print("getmoviedetails es: ", response.json())

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve search results.")
        return None
@lru_cache(maxsize=128)
def get_country_flag(fullname):

    url = f"https://restcountries.com/v3.1/name/{fullname}?fullText=true"
    response = requests.get(url)
    # print("get_country_flag es: ", response.json())

    if response.status_code == 200:
        country_data = response.json()
        if country_data:
            return country_data[0].get("flags", {}).get("svg", None)
    print(f"Failed to retrieve flag for country code: {fullname}")
    return None


def merge_data_with_flags(filter):
    filmssearch = searchfilms(filter)
    moviesdetailswithflags = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        
        for movie in filmssearch.get("Search", []):
            futures.append(executor.submit(getmoviedetails, movie))
        
        for future in concurrent.futures.as_completed(futures):
            moviedetails = future.result()
            if moviedetails:
                countries_names = moviedetails["Country"].split(",")
                countries = []
                for country in countries_names:
                    country_name = country.strip()
                    flag = get_country_flag(country_name)
                    countries.append({"name": country_name, "flag": flag})

                moviewithflags = {
                    "title": moviedetails["Title"],
                    "year": moviedetails["Year"],
                    "countries": countries
                }
                moviesdetailswithflags.append(moviewithflags)
    
    return moviesdetailswithflags

@app.route("/")
def index():
    filter = request.args.get("filter", "").upper()
    return render_template("index.html", movies = merge_data_with_flags(filter))

@app.route("/api/movies")
def api_movies():
    filter = request.args.get("filter", "")
    return jsonify(merge_data_with_flags(filter))    

if __name__ == "__main__":
    app.run(debug=True)
