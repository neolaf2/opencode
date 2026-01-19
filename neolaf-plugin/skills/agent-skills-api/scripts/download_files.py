"""
Helper functions for downloading files created by Agent Skills.

Usage:
    from download_files import extract_file_ids, download_files
    
    # Extract file IDs from response
    file_ids = extract_file_ids(response)
    
    # Download files
    download_files(client, file_ids, output_dir="./outputs")
"""

import anthropic
from pathlib import Path
from typing import List


def extract_file_ids(response) -> List[str]:
    """
    Extract file IDs from an Agent Skills API response.
    
    Args:
        response: Response object from client.beta.messages.create()
        
    Returns:
        List of file IDs found in the response
    """
    file_ids = []
    
    for item in response.content:
        if item.type == 'bash_code_execution_tool_result':
            content_item = item.content
            if content_item.type == 'bash_code_execution_result':
                for file in content_item.content:
                    if hasattr(file, 'file_id'):
                        file_ids.append(file.file_id)
    
    return file_ids


def download_files(client: anthropic.Anthropic, 
                  file_ids: List[str], 
                  output_dir: str = "./outputs",
                  verbose: bool = True) -> List[Path]:
    """
    Download files using the Files API.
    
    Args:
        client: Anthropic client instance
        file_ids: List of file IDs to download
        output_dir: Directory to save downloaded files
        verbose: Whether to print progress messages
        
    Returns:
        List of Path objects for downloaded files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    
    for file_id in file_ids:
        try:
            # Get file metadata
            metadata = client.beta.files.retrieve_metadata(
                file_id=file_id,
                betas=["files-api-2025-04-14"]
            )
            
            # Download file content
            content = client.beta.files.download(
                file_id=file_id,
                betas=["files-api-2025-04-14"]
            )
            
            # Save to disk
            filepath = output_path / metadata.filename
            content.write_to_file(str(filepath))
            
            downloaded_files.append(filepath)
            
            if verbose:
                size_kb = metadata.size_bytes / 1024
                print(f"✅ Downloaded: {filepath} ({size_kb:.2f} KB)")
                
        except anthropic.NotFoundError:
            if verbose:
                print(f"❌ File not found: {file_id}")
        except Exception as e:
            if verbose:
                print(f"❌ Error downloading {file_id}: {e}")
    
    return downloaded_files


def download_from_response(client: anthropic.Anthropic,
                           response,
                           output_dir: str = "./outputs",
                           verbose: bool = True) -> List[Path]:
    """
    Extract file IDs from response and download all files.
    
    Args:
        client: Anthropic client instance
        response: Response object from client.beta.messages.create()
        output_dir: Directory to save downloaded files
        verbose: Whether to print progress messages
        
    Returns:
        List of Path objects for downloaded files
    """
    file_ids = extract_file_ids(response)
    
    if not file_ids:
        if verbose:
            print("⚠️  No files found in response")
        return []
    
    if verbose:
        print(f"📥 Found {len(file_ids)} file(s) to download")
    
    return download_files(client, file_ids, output_dir, verbose)


def list_all_files(client: anthropic.Anthropic, verbose: bool = True) -> List[dict]:
    """
    List all files available via the Files API.
    
    Args:
        client: Anthropic client instance
        verbose: Whether to print file information
        
    Returns:
        List of file metadata dictionaries
    """
    files = client.beta.files.list(betas=["files-api-2025-04-14"])
    
    file_list = []
    for file in files.data:
        file_info = {
            "id": file.id,
            "filename": file.filename,
            "size_bytes": file.size_bytes,
            "created_at": file.created_at
        }
        file_list.append(file_info)
        
        if verbose:
            size_kb = file.size_bytes / 1024
            print(f"📄 {file.filename} ({size_kb:.2f} KB) - {file.created_at}")
    
    return file_list


def delete_file(client: anthropic.Anthropic, 
                file_id: str,
                verbose: bool = True) -> bool:
    """
    Delete a file from the Files API.
    
    Args:
        client: Anthropic client instance
        file_id: ID of the file to delete
        verbose: Whether to print status messages
        
    Returns:
        True if deletion successful, False otherwise
    """
    try:
        client.beta.files.delete(
            file_id=file_id,
            betas=["files-api-2025-04-14"]
        )
        
        if verbose:
            print(f"✅ Deleted file: {file_id}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"❌ Error deleting {file_id}: {e}")
        return False


# Example usage
if __name__ == "__main__":
    import os
    
    # Initialize client
    client = anthropic.Anthropic()
    
    # Example 1: Extract and download files from a response
    print("Example 1: Download files from response")
    print("=" * 60)
    
    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        betas=["code-execution-2025-08-25", "skills-2025-10-02"],
        container={
            "skills": [
                {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
            ]
        },
        messages=[{
            "role": "user",
            "content": "Create a simple budget spreadsheet with income and expenses"
        }],
        tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
    )
    
    # Download files
    downloaded = download_from_response(client, response, output_dir="./examples")
    print(f"\n📦 Downloaded {len(downloaded)} file(s)\n")
    
    # Example 2: List all files
    print("Example 2: List all available files")
    print("=" * 60)
    all_files = list_all_files(client)
    print(f"\n📋 Total files: {len(all_files)}\n")
    
    # Example 3: Manual download with file IDs
    print("Example 3: Manual download")
    print("=" * 60)
    file_ids = extract_file_ids(response)
    if file_ids:
        download_files(client, file_ids, output_dir="./manual_downloads")
