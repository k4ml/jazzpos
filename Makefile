
clear_orig:
	find . -name '*.orig' | xargs rm

clean:
	rm -rf eggs bin develop develop-eggs .installed.cfg parts
