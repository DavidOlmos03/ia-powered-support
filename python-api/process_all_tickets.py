#!/usr/bin/env python
"""Script to process all unprocessed tickets."""

import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Get unprocessed tickets
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

tickets = client.table('tickets').select('*').eq('processed', False).execute().data

print(f'Found {len(tickets)} unprocessed tickets\n')

# Process each ticket via API
import httpx

async def process_tickets():
    api_key = os.getenv('API_KEY')

    async with httpx.AsyncClient(timeout=60.0) as http_client:
        for i, ticket in enumerate(tickets, 1):
            print(f"[{i}/{len(tickets)}] Processing ticket: {ticket['id']}")
            print(f"  Description: {ticket['description'][:60]}...")

            try:
                response = await http_client.post(
                    'http://localhost:8000/api/v1/process-ticket',
                    json={
                        'ticket_id': ticket['id'],
                        'description': ticket['description']
                    },
                    headers={
                        'Content-Type': 'application/json',
                        'X-API-Key': api_key
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ Success! Category: {result['classification']['category']}, Sentiment: {result['classification']['sentiment']}")
                else:
                    print(f"  ❌ Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"  ❌ Exception: {e}")

            print()

asyncio.run(process_tickets())
print("Done!")
