import json
import urllib.parse
import boto3
import io
import os
from neo4j import GraphDatabase

s3_client = boto3.client('s3')

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
driver = None
if NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def search_products(product_name):
    if not driver:
        print("Neo4j driver not initialized.")
        return []

    print(f"Searching for products related to: {product_name}")
    query = """
    MATCH (p:Product {name: $productName})<-[:CONTAINS]-(t:Ticket)-[:CONTAINS]->(other:Product)
    WHERE other.name <> $productName
    RETURN other.name AS product, count(t) AS frequency
    ORDER BY frequency DESC
    LIMIT 5
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, productName=product_name)
            return [record["product"] for record in result]
    except Exception as e:
        print(f"Error querying Neo4j: {e}")
        raise e

def main(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    product_name = None
    if event and 'queryStringParameters' in event and event['queryStringParameters']:
        product_name = event['queryStringParameters'].get('product')
    
    if not product_name:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing "product" query parameter'})
        }

    try:
        recommendations = search_products(product_name)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'product': product_name,
                'recommendations': recommendations
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

