try:
    # Pakai sertifikat Windows/OS, supaya jalan di jaringan kantor yang memeriksa HTTPS dengan sertifikat sendiri.
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass
