from googlesearch import search

query = "Moves Like Jagger" + " genius"

results = search(query, tld="co.in", num=5, stop=10, pause=2)
lyric_link = ''

for link in results:
    if 'genius' in link:
        lyric_link = link
        break

print(lyric_link)