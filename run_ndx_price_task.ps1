$ErrorActionPreference = "Stop"

$projectPath = "C:\Users\ace\Desktop\found_quant"
$pythonPath = "C:\Users\ace\AppData\Local\Programs\Python\Python315\python.exe"
$scriptPath = Join-Path $projectPath "ndx_price.py"
$logPath = Join-Path $projectPath "ndx_price_task.log"

# 任务计划程序不会依赖 VS Code 的终端环境；这里显式加载用户级 Token 和代理。
$pushplusToken = [Environment]::GetEnvironmentVariable("PUSHPLUS_TOKEN", "User")
if ([string]::IsNullOrWhiteSpace($pushplusToken)) {
    "$(Get-Date -Format s) 未找到用户级 PUSHPLUS_TOKEN，任务未运行。" |
        Out-File -FilePath $logPath -Append -Encoding utf8
    exit 2
}

$env:PUSHPLUS_TOKEN = $pushplusToken
$env:HTTP_PROXY = "http://127.0.0.1:7897"
$env:HTTPS_PROXY = "http://127.0.0.1:7897"
Set-Location $projectPath

try {
    # 让 cmd 直接重定向 Python 的 UTF-8 输出，避免 Windows PowerShell 5.1 转码乱码。
    $commandLine = '"' + $pythonPath + '" "' + $scriptPath + '" > "' + $logPath + '" 2>&1'
    & $env:ComSpec /d /c $commandLine
    exit $LASTEXITCODE
}
catch {
    "$(Get-Date -Format s) 启动脚本失败：$($_.Exception.Message)" |
        Out-File -FilePath $logPath -Append -Encoding utf8
    exit 1
}



