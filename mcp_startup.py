"""
MCP Server Startup Script
Starts all MCP servers for the application
"""
import asyncio
import subprocess
import sys
import time
import os
from typing import List, Dict

class MCPServerManager:
    def __init__(self):
        self.servers = {
            'database': {
                'script': 'mcp/servers/database_server.py',
                'process': None,
                'description': 'Database operations server'
            },
            'vector': {
                'script': 'mcp/servers/vector_server.py',
                'process': None,
                'description': 'Vector store operations server'
            },
            'image': {
                'script': 'mcp/servers/image_server.py',
                'process': None,
                'description': 'Image generation and processing server'
            },
            'web_search': {
                'script': 'mcp/servers/web_search_server.py',
                'process': None,
                'description': 'Web search operations server'
            }
        }

    def start_server(self, server_name: str) -> bool:
        """Start a single MCP server"""
        try:
            if server_name not in self.servers:
                print(f"❌ Unknown server: {server_name}")
                return False

            server_config = self.servers[server_name]
            script_path = server_config['script']

            if not os.path.exists(script_path):
                print(f"❌ Server script not found: {script_path}")
                return False

            print(f"🚀 Starting {server_name} MCP server...")
            
            # Start the server process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            server_config['process'] = process
            
            # Give the server a moment to start
            time.sleep(1)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {server_name} MCP server started successfully (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {server_name} MCP server failed to start")
                print(f"   stdout: {stdout}")
                print(f"   stderr: {stderr}")
                return False

        except Exception as e:
            print(f"❌ Error starting {server_name} server: {str(e)}")
            return False

    def stop_server(self, server_name: str) -> bool:
        """Stop a single MCP server"""
        try:
            if server_name not in self.servers:
                print(f"❌ Unknown server: {server_name}")
                return False

            server_config = self.servers[server_name]
            process = server_config['process']

            if process and process.poll() is None:
                print(f"🛑 Stopping {server_name} MCP server...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"✅ {server_name} MCP server stopped gracefully")
                except subprocess.TimeoutExpired:
                    print(f"⚠️  Force killing {server_name} MCP server...")
                    process.kill()
                    process.wait()
                    print(f"✅ {server_name} MCP server force stopped")

                server_config['process'] = None
                return True
            else:
                print(f"ℹ️  {server_name} MCP server is not running")
                return True

        except Exception as e:
            print(f"❌ Error stopping {server_name} server: {str(e)}")
            return False

    def start_all_servers(self) -> Dict[str, bool]:
        """Start all MCP servers"""
        print("🚀 Starting all MCP servers...")
        results = {}
        
        for server_name in self.servers:
            results[server_name] = self.start_server(server_name)
        
        successful = sum(results.values())
        total = len(results)
        
        print(f"\n📊 MCP Server Startup Summary:")
        print(f"   ✅ Successful: {successful}/{total}")
        print(f"   ❌ Failed: {total - successful}/{total}")
        
        if successful == total:
            print("🎉 All MCP servers started successfully!")
        elif successful > 0:
            print("⚠️  Some MCP servers failed to start")
        else:
            print("💥 All MCP servers failed to start")
        
        return results

    def stop_all_servers(self) -> Dict[str, bool]:
        """Stop all MCP servers"""
        print("🛑 Stopping all MCP servers...")
        results = {}
        
        for server_name in self.servers:
            results[server_name] = self.stop_server(server_name)
        
        successful = sum(results.values())
        total = len(results)
        
        print(f"\n📊 MCP Server Shutdown Summary:")
        print(f"   ✅ Successful: {successful}/{total}")
        print(f"   ❌ Failed: {total - successful}/{total}")
        
        return results

    def get_server_status(self) -> Dict[str, Dict]:
        """Get status of all servers"""
        status = {}
        
        for server_name, config in self.servers.items():
            process = config['process']
            if process and process.poll() is None:
                status[server_name] = {
                    'running': True,
                    'pid': process.pid,
                    'description': config['description']
                }
            else:
                status[server_name] = {
                    'running': False,
                    'pid': None,
                    'description': config['description']
                }
        
        return status

    def print_status(self):
        """Print current status of all servers"""
        print("\n📊 MCP Server Status:")
        print("=" * 50)
        
        status = self.get_server_status()
        
        for server_name, info in status.items():
            status_icon = "✅" if info['running'] else "❌"
            pid_info = f"(PID: {info['pid']})" if info['pid'] else "(Not running)"
            
            print(f"   {status_icon} {server_name:<12} {pid_info:<15} - {info['description']}")
        
        running_count = sum(1 for info in status.values() if info['running'])
        total_count = len(status)
        
        print(f"\n   Running: {running_count}/{total_count} servers")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP Server Manager')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'], 
                       help='Action to perform')
    parser.add_argument('--server', help='Specific server to manage (optional)')
    
    args = parser.parse_args()
    
    manager = MCPServerManager()
    
    if args.action == 'start':
        if args.server:
            manager.start_server(args.server)
        else:
            manager.start_all_servers()
    
    elif args.action == 'stop':
        if args.server:
            manager.stop_server(args.server)
        else:
            manager.stop_all_servers()
    
    elif args.action == 'restart':
        if args.server:
            manager.stop_server(args.server)
            time.sleep(1)
            manager.start_server(args.server)
        else:
            manager.stop_all_servers()
            time.sleep(2)
            manager.start_all_servers()
    
    elif args.action == 'status':
        manager.print_status()

if __name__ == "__main__":
    main()