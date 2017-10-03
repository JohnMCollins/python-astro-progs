#! /usr/bin/perl

use Getopt::Long;
use DBI;

$dbase = DBI->connect("DBI:mysql:database=specrecords;host=nancy.toad.me.uk", "specrecs", "cz93kb77");
die "Cannot open database" unless $dbase;

$infile = "";
$source = "HARPS";
$archive = "";

GetOptions("infile=s" => \$infile, "source=s" => \$source, "archive=s" => \$archive) or die "Bad options";

die "You did not give archive" unless length($archive) != 0;

$file = \*STDIN;
if (length($infile) != 0)  {
	open(INF, $infile) or die "Cannot open $infile";
	$file = \*INF;
}

$qarch = $dbase->quote($archive);
$qsource = $dbase->quote($source);

while (<$file>) {
	chop;
	next unless /(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d\.\d+)/;
	my $date = "$1-$2-$3 $4:$5:$6";
	my $qdate = $dbase->quote($date);
	my $sfh = $dbase->prepare("INSERT INTO obs (source,archive,epoch) VALUES ($qsource,$qarch,$qdate)");
	$sfh->execute;
}


