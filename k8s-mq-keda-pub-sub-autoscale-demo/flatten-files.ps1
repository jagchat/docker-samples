param(
    [string]$SourceFolder="",
    [string]$TargetFolder=""
)

# =============================================================================
# EXCLUSION CONFIGURATION - Modify these arrays to customize what gets excluded
# =============================================================================

# Folder names to exclude (case-insensitive, exact match)
$ExcludeFolders = @(
    '.git',
    '.svn',
    'node_modules',
    'bin',
    'obj',
    '.vs',
    '.vscode',
    'Debug',
    'Release',
    'packages',
    'Temp',
    'temp',
    '__pycache__',
    '.pytest_cache',
    'dist',
    'build'
)

# File extensions to exclude (include the dot, case-insensitive)
$ExcludeFileExtensions = @(
    '.tmp',
    '.temp',
    '.log',
    '.cache',
    '.bak',
    '.swp',
    '.ds_store',
    '.thumbs.db',
    '.exe',
    '.dll',
    '.pdb'
)

# Specific file names to exclude (case-insensitive, exact match)
$ExcludeFileNames = @(
    'Thumbs.db',
    '.DS_Store',
    'desktop.ini',
    '.gitignore',
    '.gitattributes',
    'web.config',
    'app.config',
	'package-lock.json'
)

# Folder patterns to exclude (case-insensitive, wildcard patterns)
$ExcludeFolderPatterns = @(
    'backup_*',
    '*_backup',
    'old_*',
    '*_old',
    '*.tmp'
)

# Function to check if a folder should be excluded
function Test-FolderExclusion {
    param([string]$FolderName, [string]$FolderPath)
    
    # Check exact folder name matches
    if ($ExcludeFolders -contains $FolderName) {
        return $true
    }
    
    # Check folder patterns
    foreach ($Pattern in $ExcludeFolderPatterns) {
        if ($FolderName -like $Pattern) {
            return $true
        }
    }
    
    return $false
}

# Function to check if a file should be excluded
function Test-FileExclusion {
    param([System.IO.FileInfo]$File)
    
    # Check file extensions
    if ($ExcludeFileExtensions -contains $File.Extension.ToLower()) {
        return $true
    }
    
    # Check specific file names
    if ($ExcludeFileNames -contains $File.Name) {
        return $true
    }
    
    return $false
}

# Function to get filtered files (excluding files in excluded folders)
function Get-FilteredFiles {
    param([string]$Path)
    
    $FilteredFiles = @()
    $ExcludedFolders = 0
    $ExcludedFiles = 0
    
    # Get all directories first to check exclusions
    $AllDirectories = Get-ChildItem -Path $Path -Directory -Recurse
    $ExcludedDirectoryPaths = @()
    
    foreach ($Dir in $AllDirectories) {
        if (Test-FolderExclusion -FolderName $Dir.Name -FolderPath $Dir.FullName) {
            $ExcludedDirectoryPaths += $Dir.FullName
            $ExcludedFolders++
            Write-Host "EXCLUDED FOLDER: $($Dir.FullName.Substring($Path.Length).TrimStart('\', '/'))" -ForegroundColor DarkYellow
        }
    }
    
    # Get all files
    $AllFiles = Get-ChildItem -Path $Path -File -Recurse
    
    foreach ($File in $AllFiles) {
        # Check if file is in an excluded directory
        $InExcludedDirectory = $false
        foreach ($ExcludedPath in $ExcludedDirectoryPaths) {
            if ($File.FullName.StartsWith($ExcludedPath + [System.IO.Path]::DirectorySeparatorChar) -or 
                $File.FullName.StartsWith($ExcludedPath + [System.IO.Path]::AltDirectorySeparatorChar)) {
                $InExcludedDirectory = $true
                break
            }
        }
        
        if ($InExcludedDirectory) {
            continue  # Skip files in excluded directories
        }
        
        # Check if file itself should be excluded
        if (Test-FileExclusion -File $File) {
            $ExcludedFiles++
            Write-Host "EXCLUDED FILE: $($File.FullName.Substring($Path.Length).TrimStart('\', '/'))" -ForegroundColor DarkYellow
            continue
        }
        
        $FilteredFiles += $File
    }
    
    return @{
        Files = $FilteredFiles
        ExcludedFolders = $ExcludedFolders
        ExcludedFiles = $ExcludedFiles
    }
}
function Validate-Path {
    param([string]$Path, [string]$PathType)
    
    if (-not $Path) {
        throw "$PathType path cannot be empty"
    }
    
    # Convert to absolute path and normalize
    $AbsolutePath = [System.IO.Path]::GetFullPath($Path)
    
    return $AbsolutePath
}

# Function to create safe filename by replacing invalid characters
function Get-SafeFileName {
    param([string]$FileName)
    
    # Get invalid filename characters and replace them with underscores
    $InvalidChars = [System.IO.Path]::GetInvalidFileNameChars()
    $SafeName = $FileName
    
    foreach ($Char in $InvalidChars) {
        $SafeName = $SafeName -replace [regex]::Escape($Char), '_'
    }
    
    return $SafeName
}

try {
    # Validate and normalize paths
	$scriptDirectory = $PSScriptRoot
	$SourceFolder = $scriptDirectory
	$TargetFolder = "$scriptDirectory/flattened"
    $SourcePath = Validate-Path -Path $SourceFolder -PathType "Source"
    $TargetPath = Validate-Path -Path $TargetFolder -PathType "Target"
    
    # Check if source folder exists
    if (-not (Test-Path -Path $SourcePath -PathType Container)) {
        throw "Source folder does not exist: $SourcePath"
    }
    
    # Delete target folder if it exists, then create it fresh
    if (Test-Path -Path $TargetPath) {
        Write-Host "Deleting existing target folder: $TargetPath" -ForegroundColor Yellow
        Remove-Item -Path $TargetPath -Recurse -Force
    }
    
    Write-Host "Creating target folder: $TargetPath" -ForegroundColor Yellow
    New-Item -Path $TargetPath -ItemType Directory -Force | Out-Null
    
    Write-Host "Source folder: $SourcePath" -ForegroundColor Green
    Write-Host "Target folder: $TargetPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Exclusion Summary:" -ForegroundColor Cyan
    Write-Host "- Excluded folder names: $($ExcludeFolders -join ', ')" -ForegroundColor DarkCyan
    Write-Host "- Excluded file extensions: $($ExcludeFileExtensions -join ', ')" -ForegroundColor DarkCyan
    Write-Host "- Excluded file names: $($ExcludeFileNames -join ', ')" -ForegroundColor DarkCyan
    Write-Host "- Excluded folder patterns: $($ExcludeFolderPatterns -join ', ')" -ForegroundColor DarkCyan
    Write-Host ""
    
    # Get filtered files (excluding specified folders and files)
    Write-Host "Scanning files and applying exclusions..." -ForegroundColor Cyan
    $FilterResult = Get-FilteredFiles -Path $SourcePath
    $AllFiles = $FilterResult.Files
    
    if ($AllFiles.Count -eq 0) {
        Write-Host "No files found to process after applying exclusions." -ForegroundColor Yellow
        Write-Host "Excluded $($FilterResult.ExcludedFolders) folders and $($FilterResult.ExcludedFiles) files." -ForegroundColor Yellow
        return
    }
    
    Write-Host ""
    Write-Host "Found $($AllFiles.Count) files to process (excluded $($FilterResult.ExcludedFolders) folders and $($FilterResult.ExcludedFiles) files)..." -ForegroundColor Cyan
    Write-Host ""
    
    $ProcessedCount = 0
    
    foreach ($File in $AllFiles) {
        try {
            # Get relative path from source folder
            $RelativePath = $File.FullName.Substring($SourcePath.Length).TrimStart('\', '/')
            
            # Get directory part of relative path (excluding filename)
            $RelativeDir = [System.IO.Path]::GetDirectoryName($RelativePath)
            
            # Create new filename: replace path separators with double hyphens
            if ($RelativeDir) {
                # Replace both forward and backward slashes with double hyphens
                $PathPrefix = $RelativeDir -replace '[\\/]', '--'
                $NewFileName = "$PathPrefix--$($File.Name)"
            } else {
                # File is in root of source folder
                $NewFileName = $File.Name
            }
            
            # Make sure filename is safe for filesystem
            $SafeFileName = Get-SafeFileName -FileName $NewFileName
            
            # Construct target file path
            $TargetFilePath = Join-Path -Path $TargetPath -ChildPath $SafeFileName
            

            
            # Copy file to target location
            Copy-Item -Path $File.FullName -Destination $TargetFilePath -Force
            
            Write-Host "COPIED: $($File.Name) -> $SafeFileName" -ForegroundColor Green
            $ProcessedCount++
            
        } catch {
            Write-Host "ERROR processing file '$($File.FullName)': $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
    Write-Host "Files processed: $ProcessedCount" -ForegroundColor Green
    Write-Host "Folders excluded: $($FilterResult.ExcludedFolders)" -ForegroundColor Yellow
    Write-Host "Files excluded: $($FilterResult.ExcludedFiles)" -ForegroundColor Yellow
    Write-Host "Total files found: $($AllFiles.Count)" -ForegroundColor Cyan
    Write-Host "Operation completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}