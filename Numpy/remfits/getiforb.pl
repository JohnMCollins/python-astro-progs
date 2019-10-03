#! /usr/bin/perl

# @Author: John M Collins <jmc>
# @Date:   2018-03-24T14:39:41+00:00
# @Email:  jmc@toad.me.uk
# @Filename: getfits.pl
# @Last modified by:   jmc
# @Last modified time: 2019-01-18T20:38:19+00:00

use dbops;
use Getopt::Long;
use remdefaults;
use progress;

my $base = remdefaults::default_database;
my $verbose = 0;

GetOptions("database=s" => \$base, "verbose" => \$verbose) or die "Invalid options expecting --database dbase";

my $dbase = dbops::opendb($base) or die "Cannot open DB $base";

if ($verbose)  {
    $sfh = $dbase->prepare("SELECT COUNT(*) FROM iforbinf WHERE ind=0 AND rejreason IS NULL");
    $sfh->execute;
    my $row = $sfh->fetchrow_arrayref();
    my ($limit) = @$row;
    $prog = progress->new(-limit => $limit);
}

$sfh = $dbase->prepare("SELECT iforbind,ffname FROM iforbinf WHERE ind=0 AND rejreason IS NULL ORDER by date_obs");
$sfh->execute;

$root_url = 'http://ross.iasfbo.inaf.it';

my $count = 0;
my $errors = 0;

while (my $row = $sfh->fetchrow_arrayref())  {
	$count++;
    my ($iforbind, $ffname) = @$row;
    my $fitsfile = "";
    my $next;
    open(WG, "wget -q -O - $root_url/REMDBdev/fits_retrieve.php?ffile=/Ross/$ffname|") or die "Cannot create pipe";
    while (sysread(WG,$next,4096) > 0)  {
	   $fitsfile .=	$next;
    }
    close WG;
    if (length($fitsfile) < 10000 || (substr $fitsfile, 0, 6) eq '<html>')  {
    	my $sfh = $dbase->prepare("UPDATE iforbinf SET rejreason='FITS file not found' WHERE iforbind=$iforbind");
        $sfh->execute;
        print STDERR "Could not fetch $ffname\n";
        $errors++;
        next;
    }
    my $iq = $dbase->prepare("INSERT INTO fitsfile (fitsgz) VALUES (?)");
    $iq->execute($fitsfile);
    $iq = $dbase->prepare("SELECT LAST_INSERT_ID()");
    $iq->execute;
    my $rr = $iq->fetchrow_arrayref();
    my $ind = $rr->[0];
    $iq = $dbase->prepare("UPDATE iforbinf SET ind=$ind WHERE iforbind=$iforbind");
    $iq->execute;
    $prog->update($count) if $verbose;
}
$prog->finish if $verbose;
print STDERR "$count daily flat/bias FITS files loaded";
print STDERR " 1 error" if $errors == 1;
print STDERR " $errors errors" if $errors > 1;
print STDERR "\n";

