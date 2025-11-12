# Script to generate and manage multiple localnet neo-cli nodes
# Usage: .\run-localnet-nodes.ps1 [start|stop|status|clean] [node_count] [base_port] [base_rpc_port]

$ErrorActionPreference = "Stop"

# Configuration
$NODE_COUNT = if ($args[1]) { [int]$args[1] } else { 7 }
$BASE_PORT = if ($args[2]) { [int]$args[2] } else { 20333 }
$BASE_RPC_PORT = if ($args[3]) { [int]$args[3] } else { 10330 }
$BASE_DATA_DIR = "localnet_nodes"

$DOTNET_VERSION = "net10.0"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$NEO_CLI_DIR = if ($env:NEO_CLI_DIR) { $env:NEO_CLI_DIR } else { Join-Path $SCRIPT_DIR "..\..\neo\bin\Neo.CLI\$DOTNET_VERSION" }

# Logging functions
function log_info {
    param([string]$message)
    Write-Host "[INFO] $message" -ForegroundColor Blue
}

function log_success {
    param([string]$message)
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

function log_warning {
    param([string]$message)
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

function log_error {
    param([string]$message)
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

# Check if neo-cli exists
function check_neo_cli {
    log_info "Using NEO_CLI_DIR: $NEO_CLI_DIR"
    $neoCliExe = Join-Path $NEO_CLI_DIR "neo-cli"
    $neoCliDll = Join-Path $NEO_CLI_DIR "neo-cli.dll"
    
    if (-not (Test-Path $neoCliExe) -and -not (Test-Path $neoCliDll)) {
        log_error "neo-cli not found in $NEO_CLI_DIR"
        log_info "Please build the project first: dotnet build"
        log_info "Or set NEO_CLI_DIR environment variable to the correct path"
        exit 1
    }
}

# An Array of addresses, NOTE: just for test
$ADDRESSES = @(
    "NSL83LVKbvCpg5gjWC9bfsmERN5kRJSs9d",
    "NRPf2BLaP595UFybH1nwrExJSt5ZGbKnjd",
    "NXRrR4VU3TJyZ6iPBfvoddRKAGynVPvjKm",
    "NfGwaZPHGXLqZ17U7p5hqkZGivArXbXUbL",
    "NjCgqnnJpCsRQwEayWy1cZSWVwQ7eRejRq",
    "NYXoVMFa3ekGUnX4qzk8DTD2hhs5aSh2k4",
    "NQSjfdeawkxqcUXQ3Vvbka66Frr4hQJoBr"
)

# An Array of keys
$KEYS = @(
    "6PYVdEBZe7Mg4CiikuCXkEpcbwX7WXT72xfHTYd6hJzRWN3iBPDfGis7kV",
    "6PYNZ7WDsjXwn2Mo8T3N7fTw7ZSfY71MXbVeRf1zZjv2baEdjbWNHm5mGQ",
    "6PYXGkpWLLXtyC6cQthCcShioQJupRvyhDrz6xfLyiEa9HeJW4oTb4aJHP",
    "6PYUCCNgCrVrB5vpCbsFwzEA7d2SkCzCTYMyhYw2TL51CaGeie2UWyehzw",
    "6PYQpWR6CGrWDKauPWfVEfmwMKp2xKFod4X1AvV39ud5qhaSkrsFQeCBPy",
    "6PYTm6sJLR1oWX2svdJkzWhkbqTAGurEybDdcCTBa19WNzDuFXURX2NAaE",
    "6PYQM2Tdkon4kqzYSboctKLEXyLLub4vQFSXVwwgtSPcPTsqC2VhQXwf5R"
)

# An Array of scripts
$SCRIPTS = @(
    "DCEChSZdyIWdBeHkKpDWwpqd4VUx6sGCSJdD5qlHgX0qn2ZBVuezJw==",
    "DCECozKyXb9hGPwlv2Tw2DALu2I7eDRDcazwy1ByffMtnbNBVuezJw==",
    "DCECqgIsK8NhTSOvwSFvxD2tkHINHilrTgm37izZvrgNm+pBVuezJw==",
    "DCEDabXhB8SMjperdGnbbr8JAZz7MiPToYxK+iFwQoE9+d5BVuezJw==",
    "DCECnkPTdNxK3KFYu0ZbSthBegdmQaU5UOPLccY0PdJYk9RBVuezJw==",
    "DCEChLsd71mcGde7lMvdiOx+1IXbId6mTIa7kXYi+1ac6cpBVuezJw==",
    "DCED5FrD4mtUqJfwU41g1MwcKIS43Zk78Ie+REaoLdQE/9hBVuezJw=="
)

# Generate configuration for a specific node
function generate_node_config {
    param([int]$node_id)
    
    $port = $BASE_PORT + $node_id
    $rpc_port = $BASE_RPC_PORT + $node_id
    $data_dir = Join-Path $BASE_DATA_DIR "node_$node_id"
    $config_file = Join-Path $data_dir "config.json"
    $wallet_file = Join-Path $data_dir "wallet.json"

    log_info "Generating config for node $node_id (port: $port, rpc: $rpc_port)"
    
    # Create data directory
    New-Item -ItemType Directory -Force -Path $data_dir | Out-Null

    # Generate seed list (all other nodes)
    $seed_list = @()
    for ($i = 0; $i -lt $NODE_COUNT; $i++) {
        $seed_port = $BASE_PORT + $i
        $seed_list += "localhost:$seed_port"
    }
    
    # Create configuration file
    $configJson = @{
        ApplicationConfiguration = @{
            Logger = @{
                Path = "Logs"
                ConsoleOutput = $true
                Active = $true
            }
            Storage = @{
                Engine = "LevelDBStore"
                Path = "Data_LevelDB_Node$node_id"
            }
            P2P = @{
                Port = $port
                EnableCompression = $true
                MinDesiredConnections = 3
                MaxConnections = 10
                MaxKnownHashes = 1000
                MaxConnectionsPerAddress = 3
            }
            UnlockWallet = @{
                Path = "wallet.json"
                Password = "123"
                IsActive = $true
            }
            Contracts = @{
                NeoNameService = "0x50ac1c37690cc2cfc594472833cf57505d5f46de"
            }
            Plugins = @{
                DownloadUrl = "https://api.github.com/repos/neo-project/neo/releases"
            }
        }
        ProtocolConfiguration = @{
            Network = 1234567890
            AddressVersion = 53
            MillisecondsPerBlock = 15000
            MaxTransactionsPerBlock = 5000
            MemoryPoolMaxTransactions = 50000
            MaxTraceableBlocks = 2102400
            Hardforks = @{
                HF_Aspidochelone = 1
                HF_Basilisk = 1
                HF_Cockatrice = 1
                HF_Domovoi = 1
                HF_Echidna = 1
                HF_Faun = 1
            }
            InitialGasDistribution = 5200000000000000
            ValidatorsCount = 7
            StandbyCommittee = @(
                "0285265dc8859d05e1e42a90d6c29a9de15531eac182489743e6a947817d2a9f66",
                "02a332b25dbf6118fc25bf64f0d8300bbb623b78344371acf0cb50727df32d9db3",
                "02aa022c2bc3614d23afc1216fc43dad90720d1e296b4e09b7ee2cd9beb80d9bea",
                "0369b5e107c48c8e97ab7469db6ebf09019cfb3223d3a18c4afa217042813df9de",
                "029e43d374dc4adca158bb465b4ad8417a076641a53950e3cb71c6343dd25893d4",
                "0284bb1def599c19d7bb94cbdd88ec7ed485db21dea64c86bb917622fb569ce9ca",
                "03e45ac3e26b54a897f0538d60d4cc1c2884b8dd993bf087be4446a82dd404ffd8"
            )
            SeedList = $seed_list
        }
    }
    
    # Convert to JSON with proper formatting
    $jsonContent = $configJson | ConvertTo-Json -Depth 10
    
    Set-Content -Path $config_file -Value $jsonContent

    # Create wallet file
    $walletJson = @{
        name = "node_$node_id"
        version = "1.0"
        scrypt = @{
            n = 2
            r = 1
            p = 1
        }
        accounts = @(
            @{
                address = $ADDRESSES[$node_id]
                isDefault = $true
                lock = $false
                key = $KEYS[$node_id]
                contract = @{
                    script = $SCRIPTS[$node_id]
                    parameters = @(
                        @{
                            name = "signature"
                            type = "Signature"
                        }
                    )
                    deployed = $false
                }
            }
        )
    }
    
    $walletContent = $walletJson | ConvertTo-Json -Depth 10
    Set-Content -Path $wallet_file -Value $walletContent

    log_success "Generated config for node $node_id"
}

function initialize_plugins {
    $plugins = @("DBFTPlugin", "RpcServer", "ApplicationLogs")
    
    foreach ($plugin in $plugins) {
        $plugin_dir = Join-Path $NEO_CLI_DIR "..\..\Neo.Plugins.$plugin\$DOTNET_VERSION"
        $plugin_target_dir = Join-Path $NEO_CLI_DIR "Plugins\$plugin"
        
        if (-not (Test-Path $plugin_target_dir)) {
            New-Item -ItemType Directory -Force -Path $plugin_target_dir | Out-Null
        }

        $pluginDll = Join-Path $plugin_dir "$plugin.dll"
        if (Test-Path $pluginDll) {
            Copy-Item -Path $pluginDll -Destination (Join-Path $plugin_target_dir "$plugin.dll") -Force
        }

        $pluginJson = Join-Path $plugin_dir "$plugin.json"
        if (Test-Path $pluginJson) {
            Copy-Item -Path $pluginJson -Destination (Join-Path $plugin_target_dir "$plugin.json") -Force
        }
    }
}

# Update plugin configuration files to use local test network ID
function update_plugin_configs {
    log_info "Updating plugin configurations for local test network..."

    # Find and update all plugin JSON files in the Plugins directory under NEO_CLI_DIR
    $pluginsDir = Join-Path $NEO_CLI_DIR "Plugins"
    if (Test-Path $pluginsDir) {
        $pluginFiles = Get-ChildItem -Path $pluginsDir -Filter "*.json" -Recurse -File
        
        foreach ($plugin_file in $pluginFiles) {
            $content = Get-Content -Path $plugin_file.FullName -Raw
            if ($content -match '"Network":') {
                $current_network = [regex]::Match($content, '"Network":\s*(\d+)').Groups[1].Value
                log_info "Updating network ID from $current_network to 1234567890 in: $($plugin_file.FullName)"
                
                $content = $content -replace '"Network":\s*\d+', '"Network": 1234567890'
                Set-Content -Path $plugin_file.FullName -Value $content -NoNewline
            }
        }
    }

    $dbftConfig = Join-Path $NEO_CLI_DIR "Plugins\DBFTPlugin\DBFTPlugin.json"
    if (Test-Path $dbftConfig) {
        $content = Get-Content -Path $dbftConfig -Raw
        $content = $content -replace '"AutoStart":\s*false', '"AutoStart": true'
        Set-Content -Path $dbftConfig -Value $content -NoNewline
    }

    log_success "Plugin configurations updated for local test network"
}

# Generate all node configurations
function generate_configs {
    param([bool]$force = $false)

    log_info "Generating configurations for $NODE_COUNT nodes..."

    # Create base directory if it doesn't exist
    New-Item -ItemType Directory -Force -Path $BASE_DATA_DIR | Out-Null

    # Generate config for each node only if it doesn't exist or force regenerate
    for ($i = 0; $i -lt $NODE_COUNT; $i++) {
        $data_dir = Join-Path $BASE_DATA_DIR "node_$i"
        $config_file = Join-Path $data_dir "config.json"
        $wallet_file = Join-Path $data_dir "wallet.json"

        if ($force -or -not (Test-Path $config_file) -or -not (Test-Path $wallet_file)) {
            if ($force) {
                log_info "Force regenerating configuration for node $i..."
            }
            generate_node_config -node_id $i
        } else {
            log_info "Node $i configuration already exists, skipping..."
        }
    }

    log_success "Generated $NODE_COUNT node configurations"
}

# Start a specific node
function start_node {
    param([int]$node_id)
    
    $data_dir = Join-Path $BASE_DATA_DIR "node_$node_id"
    $config_file = Join-Path $data_dir "config.json"
    $pid_file = Join-Path $data_dir "neo.pid"

    if (Test-Path $pid_file) {
        $pid = Get-Content $pid_file
        try {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                log_warning "Node $node_id is already running (PID: $pid)"
                return
            }
        } catch {
            # Process doesn't exist, continue
        }
    }

    log_info "Starting node $node_id..."
    
    # Ensure data directory exists
    New-Item -ItemType Directory -Force -Path $data_dir | Out-Null

    # Get neo-cli executable path
    $neoCliExe = Join-Path $NEO_CLI_DIR "neo-cli"
    $neoCliDll = Join-Path $NEO_CLI_DIR "neo-cli.dll"
    
    if (-not (Test-Path $neoCliExe) -and -not (Test-Path $neoCliDll)) {
        log_error "neo-cli executable not found"
        return
    }

    # Determine which executable to use
    $logFile = Join-Path $data_dir "neo.log"
    if (Test-Path $neoCliExe) {
        $executable = $neoCliExe
        $arguments = @("--background")
    } else {
        $executable = "dotnet"
        $arguments = @($neoCliDll, "--background")
    }

    log_info "Starting $executable in $data_dir"
    
    # Start neo-cli in background with output redirected to log file
    try {
        # Use Start-Process for background execution (PowerShell equivalent of nohup)
        # Note: Some PowerShell versions may require separate files for stdout/stderr
        # If both redirections to the same file don't work, stderr will be in a separate file
        $stderrLog = $logFile -replace '\.log$', '.err.log'
        $process = Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $data_dir `
            -WindowStyle Hidden -PassThru -RedirectStandardOutput $logFile -RedirectStandardError $stderrLog
        
        $pid = $process.Id
        log_info "node $node_id started with pid $pid"
        Set-Content -Path $pid_file -Value $pid
        
        # Wait a moment and check if process is still running
        Start-Sleep -Seconds 1
        try {
            $checkProcess = Get-Process -Id $pid -ErrorAction Stop
            log_success "Node $node_id started (PID: $pid)"
        } catch {
            log_error "Failed to start node $node_id"
            if (Test-Path $pid_file) {
                Remove-Item $pid_file -Force
            }
            return
        }
    } catch {
        log_error "Failed to start node $node_id: $_"
        if (Test-Path $pid_file) {
            Remove-Item $pid_file -Force
        }
        return
    }
}

# Start all nodes
function start_nodes {
    log_info "Starting $NODE_COUNT localnet nodes..."

    check_neo_cli # Check if neo-cli exists
    initialize_plugins # Initialize required plugins
    generate_configs # Always generate configs to ensure they're up to date
    update_plugin_configs # Update plugin configuration files to use local test network ID

    # Start each node
    for ($i = 0; $i -lt $NODE_COUNT; $i++) {
        # set RpcServer Port to BASE_RPC_PORT + node_id
        $rpcServerConfig = Join-Path $NEO_CLI_DIR "Plugins\RpcServer\RpcServer.json"
        if (Test-Path $rpcServerConfig) {
            $rpc_port = $BASE_RPC_PORT + $i
            $content = Get-Content -Path $rpcServerConfig -Raw
            $content = $content -replace '"Port":\s*\d+', "`"Port`": $rpc_port"
            Set-Content -Path $rpcServerConfig -Value $content -NoNewline
        }

        start_node -node_id $i
        Start-Sleep -Seconds 1  # Small delay between starts
    }
    
    log_success "All nodes started!"
    show_status
}

# Stop a specific node
function stop_node {
    param([int]$node_id)
    
    $pid_file = Join-Path $BASE_DATA_DIR "node_$node_id\neo.pid"

    if (Test-Path $pid_file) {
        $pid = [int](Get-Content $pid_file)
        try {
            $process = Get-Process -Id $pid -ErrorAction Stop
            log_info "Stopping node $node_id (PID: $pid)..."
            Stop-Process -Id $pid -Force
            Remove-Item $pid_file -Force
            log_success "Node $node_id stopped"
        } catch {
            log_warning "Node $node_id was not running"
            Remove-Item $pid_file -Force -ErrorAction SilentlyContinue
        }
    } else {
        log_warning "Node $node_id is not running"
    }
}

# Stop all nodes
function stop_nodes {
    log_info "Stopping all localnet nodes..."

    for ($i = 0; $i -lt $NODE_COUNT; $i++) {
        stop_node -node_id $i
    }

    log_success "All nodes stopped!"
}

# Show status of all nodes
function show_status {
    log_info "Localnet nodes status:"
    Write-Host "----------------------------------------------"

    # if RpcServer plugin not installed, don't show RPC port
    $rpcServerConfig = Join-Path $NEO_CLI_DIR "Plugins\RpcServer\RpcServer.json"
    $show_rpc_port = Test-Path $rpcServerConfig

    if ($show_rpc_port) {
        Write-Host ("{0,-8} {1,-8} {2,-12} {3,-8} {4,-8}" -f "Node", "Status", "PID", "Port", "RPC")
    } else {
        Write-Host ("{0,-8} {1,-8} {2,-12} {3,-8}" -f "Node", "Status", "PID", "Port")
    }
    Write-Host "----------------------------------------------"

    for ($i = 0; $i -lt $NODE_COUNT; $i++) {
        $pid_file = Join-Path $BASE_DATA_DIR "node_$i\neo.pid"
        $port = $BASE_PORT + $i
        $rpc_port = $BASE_RPC_PORT + $i
        
        if (Test-Path $pid_file) {
            $pid = Get-Content $pid_file
            try {
                $process = Get-Process -Id $pid -ErrorAction Stop
                if ($show_rpc_port) {
                    Write-Host ("{0,-8} {1,-8} {2,-12} {3,-8} {4,-8}" -f "Node$i", "Running", $pid, $port, $rpc_port)
                } else {
                    Write-Host ("{0,-8} {1,-8} {2,-12} {3,-8}" -f "Node$i", "Running", $pid, $port)
                }
            } catch {
                if ($show_rpc_port) {
                    Write-Host ("{0,-8} {1,-8} {2,-12} {3,-8} {4,-8}" -f "Node$i", "Stopped", "-", $port, $rpc_port)
                } else {
                    Write-Host ("{0,-8} {1,-8} {2,-12} {3,-8}" -f "Node$i", "Stopped", "-", $port)
                }
            }
        } else {
            if ($show_rpc_port) {
                Write-Host ("{0,-8} {1,-8} {2,-12} {3,-8} {4,-8}" -f "Node$i", "Stopped", "-", $port, $rpc_port)
            } else {
                Write-Host ("{0,-8} {1,-8} {2,-12} {3,-8}" -f "Node$i", "Stopped", "-", $port)
            }
        }
    }
    Write-Host "----------------------------------------------"
}

# Clean up all data
function clean_data {
    log_info "Cleaning up all localnet data..."
    if (Test-Path $BASE_DATA_DIR) {
        Remove-Item -Path $BASE_DATA_DIR -Recurse -Force
    }
    log_success "All localnet data cleaned up"
}

# Show usage
function show_usage {
    $scriptName = Split-Path -Leaf $MyInvocation.ScriptName
    Write-Host "Usage: .\$scriptName [command] [node_count] [base_port] [base_rpc_port]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start     Start all localnet nodes (default: 7 nodes)"
    Write-Host "  stop      Stop all localnet nodes"
    Write-Host "  status    Show status of all nodes"
    Write-Host "  clean     Clean up all node data"
    Write-Host "  restart   Stop and start all nodes"
    Write-Host "  regenerate Force regenerate all node configurations"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  node_count    Number of nodes to start (default: 7)"
    Write-Host "  base_port     Starting P2P port (default: 20333)"
    Write-Host "  base_rpc_port Starting RPC port (default: 10330)"
    Write-Host ""
    Write-Host "Environment Variables:"
    Write-Host "  NEO_CLI_DIR    Path to neo-cli directory (default: ..\bin\Neo.CLI\$DOTNET_VERSION)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\$scriptName start                    # Start 7 nodes with default ports"
    Write-Host "  .\$scriptName start 7 30000 20000      # Start 7 nodes with P2P ports 30000-30006, RPC ports 20000-20006"
    Write-Host "  .\$scriptName status                   # Show status"
    Write-Host "  .\$scriptName stop                     # Stop all nodes"
    Write-Host "  .\$scriptName regenerate               # Force regenerate all configurations"
    Write-Host "  `$env:NEO_CLI_DIR='C:\path\to\neo-cli'; .\$scriptName start  # Use custom neo-cli path"
    Write-Host ""
}

# Main script logic
$command = if ($args[0]) { $args[0] } else { "start" }

switch ($command) {
    "start" {
        start_nodes
    }
    "stop" {
        stop_nodes
    }
    "status" {
        show_status
    }
    "clean" {
        clean_data
    }
    "restart" {
        stop_nodes
        Start-Sleep -Seconds 2
        start_nodes
    }
    "regenerate" {
        log_info "Force regenerating all node configurations..."
        check_neo_cli
        generate_configs -force $true
        update_plugin_configs
        log_success "All configurations regenerated!"
    }
    { $_ -in @("help", "-h", "--help") } {
        show_usage
    }
    default {
        log_error "Unknown command: $command"
        show_usage
        exit 1
    }
}

