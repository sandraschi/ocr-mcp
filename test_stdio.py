#!/usr/bin/env python3
"""
Test script to verify MCP server stdio communication
"""

import subprocess
import json
import time
import sys
import os

def test_stdio_communication():
    print('Testing MCP server stdio communication...')

    # Start the MCP server as a subprocess
    proc = subprocess.Popen(
        [sys.executable, '-m', 'src.ocr_mcp.server'],
        cwd=os.path.dirname(__file__),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )

    print('MCP server subprocess started')

    # Wait a bit for initialization
    time.sleep(15)
    print('Sending initialize message...')

    # Send initialize message
    init_msg = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'initialize',
        'params': {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {
                'name': 'Test Client',
                'version': '1.0.0'
            }
        }
    }

    try:
        proc.stdin.write(json.dumps(init_msg) + '\n')
        proc.stdin.flush()
        print('Initialize message sent')

        # Try to read response
        response = proc.stdout.readline().strip()
        if response:
            print(f'Response received: {response[:200]}...')

            # Try to parse as JSON
            try:
                parsed = json.loads(response)
                print('JSON response parsed successfully')
                print(f'Response ID: {parsed.get("id")}')
                print(f'Response result: {parsed.get("result", "None")}')
                print(f'Response error: {parsed.get("error", "None")}')
            except json.JSONDecodeError as e:
                print(f'JSON parse error: {e}')
        else:
            print('No response received')

    except Exception as e:
        print(f'Error communicating with MCP server: {e}')

    # Check stderr
    stderr_output = proc.stderr.read()
    if stderr_output:
        print(f'STDERR: {stderr_output[:500]}...')

    # Clean up
    proc.terminate()
    proc.wait()

if __name__ == '__main__':
    test_stdio_communication()