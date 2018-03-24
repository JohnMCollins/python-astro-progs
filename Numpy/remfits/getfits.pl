#! /usr/bin/perl

use dbops;

my $dbase = dbops::opendb('remfits') or die "Cannot open DB";

$sfh = $dbase->prepare("SELECT ffname,dithID,obsind FROM obsinf WHERE ind=0 ORDER by date_obs");
$sfh->execute;

$root_url = 'http://ross.iasfbo.inaf.it';

while (my $row = $sfh->fetchrow_arrayref())  {
    my ($ffname, $dithid, $obsind) = @$row;
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
    my $iq = $dbase->prepare("INSERT INTO fitsfile (fitsgz) VALUES (?)");
    $iq->execute($fitsfile);
    $iq = $dbase->prepare("SELECT LAST_INSERT_ID()");
    $iq->execute;
    my $rr = $iq->fetchrow_arrayref();
    my $ind = $rr->[0];
    $iq = $dbase->prepare("UPDATE obsinf SET ind=$ind WHERE obsind=$obsind");
    $iq->execute;
}
