from app.tools.alvis import alvis_search_courses
print(alvis_search_courses(
    base_url="https://strangnas.alvis.se/hittakurser",
    search="matematik",
    search_all_courses=False
).get("results", [])[:9])
