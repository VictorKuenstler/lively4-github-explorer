MODEL: commit
SELECT: (
	id,
	sha,
	children.id,
	children.sha,
	author.login
	)
WHERE: author.login >= 'a' AND author.login <= 'b'