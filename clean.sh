git config user.name "vuroxen"
git config user.email "vuroxen@gmail.com"

git checkout --orphan clean-main
git add -A
git commit -m "Initial commit"

git branch -D main
git branch -m main

echo
echo "Endi quyidagi buyruqni o'zingiz bajaring:"
echo "git push --force origin main"
