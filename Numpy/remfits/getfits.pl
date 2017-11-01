#! /usr/bin/perl

use dbops;

my $dbase = dbops::opendb('remfits') or die "Cannot open DB";

$sfh = $dbase->prepare("SELECT ind,ffname,dithID FROM obs WHERE fitsgz IS NULL ORDER by date_obs");
$sfh->execute;

$root_url = 'http://ross.iasfbo.inaf.it';

while (my $row = $sfh->fetchrow_arrayref())  {
    my $ind = $row->[0];
    my $ffname = $row->[1];
    my $dithid = $row->[2];
    if ($dithid == 0)  {
        $ffname = 'Ross/' . $ffname;
    }
    else  {
        $ffname = 'Remir/' .  $ffname;
    }
    my $fitsfile = "";
    my $next;
    open(WG, "wget -q -O - $root_url/RossDB/fits_retrieve.php?ffile=/$ffname|") or die "Cannot create pipe";
    while (sysread(WG,$next,4096) > 0)  {
	   $fitsfile .=	$next;
    }
    close WG;
    if (length($fitsfile) < 10000 || (substr $fitsfile, 0, 6) eq '<html>')  {
        print "Could not fetch $ffname\n";
        next;
    }
    my $iq = $dbase->prepare("UPDATE obs SET fitsgz=? WHERE ind=$ind");
    $iq->execute($fitsfile);
}
