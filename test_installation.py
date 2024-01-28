from src.G_graph_queries import GraphQueries

gq = GraphQueries()
df = gq._query_df(query="SHOW functions")

apoc = df.name.str.startswith('apoc').any()
n10s = df.name.str.startswith('n10s').any()
gds = df.name.str.startswith('gds').any()

if __name__ == '__main__':
    print(f"""INSTALLATIONS:
    apoc: {apoc}
    n10s: {n10s}
    graph-data-science: {gds}""")