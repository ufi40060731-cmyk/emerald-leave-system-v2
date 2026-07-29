param(
  [Parameter(Mandatory=$true)]
  [string]$RepositoryUrl
)

git init
git branch -M main
git add .
git commit -m "Initial Emerald leave system"
git remote add origin $RepositoryUrl
git push -u origin main
