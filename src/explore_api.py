import requests

r1 = requests.get('http://127.0.0.1:8000/api/events', params={'page': 1, 'per_page': 20})
data1 = r1.json()
print(f"Page 1: page={data1['page']}, per_page={data1['per_page']}, total={data1['total']}, has_more={data1['has_more']}, next_page={data1['next_page']}")
print(f"Items returned: {len(data1['items'])}")
print(data1['items'][0])

r2 = requests.get('http://127.0.0.1:8000/api/events', params={'page': 2, 'per_page': 20})
data2 = r2.json()
print(f"Page 2: page={data2['page']}, per_page={data2['per_page']}, total={data2['total']}, has_more={data2['has_more']}, next_page={data2['next_page']}")
print(f"Items returned: {len(data2['items'])}")
print(data2['items'][0])