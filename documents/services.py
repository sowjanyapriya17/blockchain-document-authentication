import hashlib


def generate_document_hash(file):

    sha256 = hashlib.sha256()

    for chunk in file.chunks():
        sha256.update(chunk)

    return sha256.hexdigest()