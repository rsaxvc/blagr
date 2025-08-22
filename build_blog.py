#!/usr/bin/python
import os
import codecs
import fileinput
import fnmatch
import glob
import shutil
feedgen_present = True
try:
	from feedgen.feed import FeedGenerator
except:
	feedgen_present = False
	print("feedgen not present or other import error, continuing. ATOM/RSS support disabled")
from datetime import datetime, timezone

#configuration
BLOG_TITLE      = "RSAXVC Development"
BLOG_SUBTITLE   = "Software, Hardware, Radios, Algorithms"
BLOG_FEED_URL   = "https://rsaxvc.net/blog/atom.xml"
BLOG_URL        = "https://rsaxvc.net/blog/"
BLOG_AUTHOR     = "rsaxvc"

PATH_BASE       = "../blog/"
POST_PATH_BASE  = PATH_BASE
TAG_PATH_BASE   = PATH_BASE + "tags/"
CSS_PATH_BASE   = PATH_BASE + "css/"
ATOM_PATH		= PATH_BASE + "atom.xml"
RSS_PATH		= PATH_BASE + "rss.xml"
PAGE_PATH_BASE	= PATH_BASE + "pages/"

POSTS_PER_PAGE	= 3

INPUT_PATH_BASE = "input/"
INPUT_CSS_PATH  = INPUT_PATH_BASE + "css/"
INPUT_POST_PATH = INPUT_PATH_BASE + "posts/"
INPUT_INC_TAIL_PATH = INPUT_PATH_BASE + "inc/tail/"

#Contains a single post
class post:
	author = ""
	title = ""
	tags = set()
	text = ""
	dt = ""
	def __cmp__(self, other):
		if( self.pdt < other.pdt ):
			return 1
		elif( self.pdt == other.pdt ):
			return 0
		else:
			return -1

	def __lt__(self, other):
		if( self.pdt < other.pdt ):
			return False
		else:
			return True

	def filter_URL( self, input ):
		output = ""
		conversion = {
			' '  : '_',
			'\'' : '',
			'\\' : '',
			'/'  : '',
			'.'  : '',
			'?'  : '',
			':'  : '',
			'>'  : '',
			}
		for char in input:
			if char in conversion:
				output += conversion[char]
			else:
				output += char
		return output

	def filter_NTFS( self, input ):
		output = ""
		conversion = {
			'\'' : '',
			'\\' : '',
			'/'  : '',
			'?'  : '',
			':'  : '',
			'>'  : '',
			}
		for char in input:
			if char in conversion:
				output += conversion[char]
			else:
				output += char
		return output

	def relpath(self):
		#When updating this, make sure to add a new entry
		#under oldpaths to add a new redirect.
		return str(self.cdt.year) + "/" + str(self.cdt.month) + "/" + str(self.cdt.day) + "/" + self.filter_URL( str(self.title) )+ ".html"

	def path(self):
		#When updating this, make sure to add a new entry
		#under oldpaths to add a new redirect.
		return POST_PATH_BASE + self.relpath()

	def oldpaths(self):
		def path0(self):
			return POST_PATH_BASE + str(self.cdt.year) + "/" + str(self.cdt.month) + "/" + str(self.cdt.day) + "/" + self.filter_NTFS(str(self.title)) + ".html"
		return [path0(self)]

	def wobpath(self):
		return BLOG_URL + self.relpath()

def parse_blagr_tophalf_line( line ):
	(first,sep,last) = line.partition(':')
	if( len(last) == 0 or len(sep) == 0 ):
		print ("error parsing file:",first)
	else:
		return (first,last.rstrip())

def parse_blagr_entry( filename ):
	"parse a blagr entry file into a structure"
	p = post()
	p.tags = set()
	post_sep_found = False
	for line in fileinput.FileInput(filename,openhook=fileinput.hook_encoded('utf-8')):
		if( post_sep_found == False ):
			if( line.rstrip() == "---" ):
				post_sep_found = True
			else:
				(chunk,text) = parse_blagr_tophalf_line( line )
				if( chunk == "Tag" ):
					p.tags.add( text )
				elif( chunk == "Author" ):
					p.author = text
				elif( chunk == "CreatedDateTime" ):
					p.cdt = datetime.strptime( text, "%Y-%m-%dT%H:%M:%S" ).replace(tzinfo=timezone.utc)
				elif( chunk == "ModifiedDateTime" ):
					p.mdt = datetime.strptime( text, "%Y-%m-%dT%H:%M:%S" ).replace(tzinfo=timezone.utc)
				elif( chunk == "PublishedDateTime" ):
					p.pdt = datetime.strptime( text, "%Y-%m-%dT%H:%M:%S" ).replace(tzinfo=timezone.utc)
				elif( chunk == "Title" ):
					p.title = text
				else:
					print ("unknown chunk type:", chunk, text)
		else:
			p.text += line
	if( not hasattr(p, 'mdt') ):
		p.mdt = p.cdt
	if( not hasattr(p, 'pdt') ):
		p.pdt = p.cdt
	return p

def globulate_tags( posts ):
	"Build a list of all tags from all posts"
	tags = set()
	for post in posts:
		for tag in post.tags:
			if tag not in tags:
				tags.add( tag )
	return list(tags)

def generate_html_redirect( f, moved_to, path_depth ):
	"Writes an html meta redirect"
	target = ( "../" * path_depth ) + moved_to
	f.write( '<html xmlns="http://www.w3.org/1999/xhtml"\n' )
	f.write( '<head>\n')
	f.write( '\t<title>Page Moved</title>\n')
	f.write( '\t<meta http-equiv="refresh" content="0;URL=\'')
	f.write( target )
	f.write( '\'" />\n')
	f.write( '</head>\n')
	f.write( '<body>\n')
	f.write( '\t<a href="' + target + '">\n')
	f.write( '\t<p>This page has moved. Click here if your browser does not support redirection</p>\n')
	f.write( '\t</a>\n' )
	f.write( '</body>\n' )
	f.write( '</html>\n' )

def generate_html_start( f, title, path_depth ):
	"Writes common header/title/css-includes/..."
	upbuffer = "../" * path_depth
	f.write( "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">\n" )
	f.write( "<html xmlns=\"http://www.w3.org/1999/xhtml\" lang=\"en\" xml:lang=\"en\">\n" )
	f.write( "<head>\n" )
	f.write( "<meta http-equiv=\"Content-type\" content=\"text/html;charset=UTF-8\" />\n")
	f.write( "<title>"+title+"</title>\n")
	f.write( '<link href="' + upbuffer + CSS_PATH_BASE + 'blog.css" rel="stylesheet" type="text/css" />')
	f.write( "</head><body>\n" )

def parse_inc_directory( dir ):
	the_text = ""
	for root, dirnames, filenames in os.walk(dir):
		for filename in fnmatch.filter(filenames, '*.inc'):
			infile = os.path.join( root, filename )
			print ("Parsing: " + infile)
			f = open( infile )
			the_text += f.read()
			f.close()
	return the_text


def generate_html_end( f, last_body_text ):
	"terminate the html document"
	f.write( last_body_text )
	f.write( "</body></html>\n" )

def write_line_link_to_post( f, post, path_depth ):
	"write html to link to a post"
	upbuffer = "../"*path_depth;
	f.write( "<li><a href=\""+upbuffer+post.path()+"\">"+post.title+"</a></li>" )

def my_open( filename, mode, encoding ):
	if not os.path.exists( os.path.dirname( filename ) ):
		os.makedirs( os.path.dirname( filename ) )
	return codecs.open(filename, mode, encoding=encoding)

def write_tag_html( tag, posts, end_text ):
	"makes the file and writes the text for a tag page"
	filename = TAG_PATH_BASE + tag + ".html"
	f = my_open(filename, 'w', 'utf-8')
	generate_html_start( f, "Tag listing for " + tag, 1 )
	f.write( "<h4>Posts tagged with " + tag + "</h4>\n" )
	f.write( "<ul>\n" )
	for post in posts:
		if tag in post.tags:
			write_line_link_to_post( f, post, 1 )
	f.write("</ul>\n")
	generate_html_end( f, end_text )
	f.close()

def generate_next_prev_links( f, path_depth, link_prev, link_next ):
	if( len( link_prev ) > 0 or len( link_next ) > 0 ):
		upbuffer = "../" * path_depth
		f.write('<div class="link_text">')
		if( len( link_prev ) > 0 ):
			f.write('<a href="' + upbuffer + link_prev + '">prev</a> ' )
		if( len( link_next ) > 0 ):
			f.write('<a href="' + upbuffer + link_next + '">next</a> ' )
		f.write('</div>')

def generate_post_html( f, post, path_depth, link_prev, link_next ):
	"makes the html for a post"
	upbuffer = "../" * path_depth
	f.write('<div class="post">')
	f.write('<h1 class="title"><a href=\"'+upbuffer+post.path()+"\">" + post.title + "</a></h1>\n" )
	f.write('<h4 class="post_date"> Written '+str(post.cdt.date())+"</h4>\n" )
	if( post.tags ):
		f.write('<h4 class="tag_list"> Tags:')
		for tag in post.tags:
			f.write( "<a href=\"" + upbuffer + TAG_PATH_BASE + tag + ".html" +"\">" + tag + "</a>&nbsp;" )
		f.write("</h4>\n")
	generate_next_prev_links( f, path_depth, link_prev, link_next )
	f.write('<div class="body_text">')
	f.write(post.text)
	f.write("</div>")
	generate_next_prev_links( f, path_depth, link_prev, link_next )
	f.write("</div>")

def write_post( post, end_text, link_prev, link_next ):
	"makes the file and writes the text for a post"
	for path in post.oldpaths():
		print ("Redirecting " + path + " to " + post.relpath())
		f = my_open( path, 'w', 'utf-8' )
		generate_html_redirect( f, post.relpath(), 3 )
		f.close()
	f = my_open( post.path(), 'w', 'utf-8' )
	generate_html_start( f, post.title, 3 )
	generate_post_html( f, post, 3, link_prev, link_next )
	generate_html_end( f, end_text )
	f.close()

def write_posts( filename, title, full_text_posts, archive_posts, end_text ):
	"writes all the posts"
	f = my_open( filename, 'w', 'utf-8' )
	generate_html_start( f, title, 0 )

	#write frontpage posts
	for post in full_text_posts:
		generate_post_html( f, post, 0, "", "" )

	if( archive_posts ):
		#write archive links
		f.write('<h1 class="title">Older</h1>\n' )
		f.write("<ul>\n");
		for post in archive_posts:
			write_line_link_to_post( f, post, 0 )
			pass
		f.write("</ul>\n");
		generate_html_end( f, end_text )
	f.close()

def filter_posts( input ):
	"""Remove posts not ready for publishing"""
	dt_utc = datetime.now().replace(tzinfo=timezone.utc)
	output = []
	for post in input:
		if( post.pdt < dt_utc ):
			output.append( post )
	return output

posts = []
for root, dirnames, filenames in os.walk(INPUT_POST_PATH):
	for filename in fnmatch.filter(filenames, '*.blagr'):
		infile = os.path.join( root, filename )
		print ("Parsing: " + infile)
		posts.append( parse_blagr_entry( infile ) )
posts.sort()

posts = filter_posts( posts )

shutil.rmtree(PATH_BASE,True)

end_text = parse_inc_directory( INPUT_INC_TAIL_PATH )

for i in range( len( posts ) ):
	link_next = ""
	link_prev = ""
	if( i != 0 ):
		link_next = posts[ i - 1 ].path()
	if( i != len( posts ) - 1 ):
		link_prev = posts[ i + 1 ].path()
	write_post( posts[i], end_text, link_prev, link_next )

index_posts = posts[:POSTS_PER_PAGE]
archive_posts = posts[POSTS_PER_PAGE:]
write_posts( POST_PATH_BASE + "index.html", BLOG_TITLE, index_posts, archive_posts, end_text )

tags = globulate_tags( posts )
tags.sort()
for tag in tags:
	write_tag_html( tag, posts, end_text )

shutil.copytree( INPUT_CSS_PATH, CSS_PATH_BASE )

if feedgen_present:
	feed = FeedGenerator()
	feed.author({'name':BLOG_AUTHOR})
	feed.link(href=BLOG_URL)
	feed.title(BLOG_TITLE)
	feed.subtitle(BLOG_SUBTITLE)

	for post in reversed(posts[0:10]):
		print(post.title)
		entry = feed.add_entry()
		entry.title(post.title)
		entry.author({'name':post.author})
		entry.id(post.wobpath())
		entry.link(href=post.wobpath())
		entry.updated(post.cdt)
		#entry.content(post.text)

	f = my_open(RSS_PATH, 'w', 'utf-8')
	f.close()
	feed.rss_file(RSS_PATH)
	#f = my_open(ATOM_PATH, 'w', 'utf-8')
	#f.write(feed.atom_str(pretty=False))
	#f.close()
